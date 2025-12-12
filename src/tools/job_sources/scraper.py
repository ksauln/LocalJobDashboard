import logging
from dataclasses import dataclass
from datetime import datetime
from typing import List, Optional, Sequence
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup

from ...models import Job
from ..parsing import strip_html
from ..dedupe import stable_job_id
from .base import BaseJobSource

logger = logging.getLogger(__name__)


@dataclass
class ProviderConfig:
    company: str
    board_id: Optional[str]
    careers_page: str


@dataclass
class ScrapedJob:
    title: str
    company: str
    location: str
    description: str
    url: str
    source: str


class BaseProvider:
    provider: str
    company: str

    def __init__(self, config: ProviderConfig):
        self.config = config
        self.company = config.company

    def fetch_jobs(self, keywords: Sequence[str], limit: Optional[int] = None) -> List[ScrapedJob]:  # pragma: no cover - network
        raise NotImplementedError


def keywords_from_query(query: str) -> List[str]:
    return [part for part in query.split() if part]


class SimpleHTMLProvider(BaseProvider):
    provider = "html"

    def __init__(self, config: ProviderConfig, search_url_template: Optional[str] = None):
        super().__init__(config)
        self.search_url_template = search_url_template or config.careers_page

    def fetch_jobs(self, keywords: Sequence[str], limit: Optional[int] = None) -> List[ScrapedJob]:  # pragma: no cover - network
        query = "+".join(keywords)
        url = self.search_url_template.format(query=query)
        resp = requests.get(url, timeout=20)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "html.parser")

        results: List[ScrapedJob] = []
        seen_urls: set[str] = set()
        for anchor in soup.find_all("a"):
            if limit and len(results) >= limit:
                break
            text = anchor.get_text(" ", strip=True)
            href = anchor.get("href")
            if not text or not href:
                continue
            absolute_url = urljoin(self.config.careers_page, href)
            if absolute_url in seen_urls or absolute_url.startswith("mailto:"):
                continue

            location = anchor.get("data-location") or ""
            description = anchor.get("title") or text
            scraped = ScrapedJob(
                title=text,
                company=self.config.company,
                location=location,
                description=description,
                url=absolute_url,
                source=self.config.careers_page,
            )
            if keywords and not any(keyword.lower() in f"{scraped.title}\n{scraped.description}".lower() for keyword in keywords):
                continue
            seen_urls.add(absolute_url)
            results.append(scraped)
        return results


class WorkdayProvider(BaseProvider):
    provider = "workday"

    def __init__(self, config: ProviderConfig, tenant: str, site: str, host: Optional[str] = None):
        super().__init__(config)
        parsed = urlparse(config.careers_page)
        self.host = host or parsed.netloc
        self.tenant = tenant
        self.site = site

    def fetch_jobs(self, keywords: Sequence[str], limit: Optional[int] = None) -> List[ScrapedJob]:  # pragma: no cover - network
        search_text = " ".join(keywords)
        api_url = f"https://{self.host}/wday/cxs/{self.tenant}/{self.site}/jobs"
        payload = {"limit": limit or 50, "offset": 0, "searchText": search_text}
        resp = requests.post(api_url, json=payload, timeout=20)
        resp.raise_for_status()
        data = resp.json()

        results: List[ScrapedJob] = []
        for job in data.get("jobPostings", []) or []:
            info = job.get("jobPostingInfo") or {}
            description = info.get("jobDescription") or info.get("subtitle") or job.get("title", "")
            location = job.get("locationsText") or info.get("location", "")
            job_url = job.get("externalUrl") or job.get("externalPath") or self.config.careers_page
            absolute_url = urljoin(self.config.careers_page, job_url)
            results.append(
                ScrapedJob(
                    title=job.get("title", ""),
                    company=self.config.company,
                    location=location,
                    description=description,
                    url=absolute_url,
                    source=self.config.careers_page,
                )
            )
            if limit and len(results) >= limit:
                break
        return results


class GreenhouseProvider(BaseProvider):
    provider = "greenhouse"

    def fetch_jobs(self, keywords: Sequence[str], limit: Optional[int] = None) -> List[ScrapedJob]:  # pragma: no cover - network
        url = f"https://boards-api.greenhouse.io/v1/boards/{self.config.board_id}/jobs?content=true"
        resp = requests.get(url, timeout=20)
        resp.raise_for_status()
        payload = resp.json()
        results: List[ScrapedJob] = []
        for job in payload.get("jobs", []):
            description = job.get("content", "")
            scraped = ScrapedJob(
                title=job.get("title", ""),
                company=self.config.company,
                location=(job.get("location") or {}).get("name", ""),
                description=description,
                url=job.get("absolute_url", self.config.careers_page),
                source=self.config.careers_page,
            )
            if keywords and not any(keyword.lower() in f"{scraped.title}\n{scraped.description}".lower() for keyword in keywords):
                continue
            results.append(scraped)
            if limit and len(results) >= limit:
                break
        return results


class AshbyProvider(BaseProvider):
    provider = "ashby"

    def fetch_jobs(self, keywords: Sequence[str], limit: Optional[int] = None) -> List[ScrapedJob]:  # pragma: no cover - network
        api_url = f"https://jobs.ashbyhq.com/api/postings/{self.config.board_id}?markdown=true"
        resp = requests.get(api_url, timeout=20)
        resp.raise_for_status()
        data = resp.json()
        results: List[ScrapedJob] = []
        for job in data.get("postings", []):
            description = job.get("description", "")
            location = job.get("locationName") or ""
            scraped = ScrapedJob(
                title=job.get("title", ""),
                company=self.config.company,
                location=location,
                description=description,
                url=job.get("jobUrl", self.config.careers_page),
                source=self.config.careers_page,
            )
            if keywords and not any(keyword.lower() in f"{scraped.title}\n{scraped.description}".lower() for keyword in keywords):
                continue
            results.append(scraped)
            if limit and len(results) >= limit:
                break
        return results


def default_providers() -> List[BaseProvider]:
    return [
        GreenhouseProvider(
            ProviderConfig(company="Unite Us", board_id="uniteus", careers_page="https://job-boards.greenhouse.io/uniteus")
        ),
        GreenhouseProvider(
            ProviderConfig(company="Komodo Health", board_id="komodohealth", careers_page="https://job-boards.greenhouse.io/komodohealth")
        ),
        GreenhouseProvider(
            ProviderConfig(company="Flatiron Health", board_id="flatironhealth", careers_page="https://flatiron.com/careers/open-positions")
        ),
        GreenhouseProvider(
            ProviderConfig(company="Databricks", board_id="databricks", careers_page="https://www.databricks.com/company/careers/open-positions")
        ),
        GreenhouseProvider(
            ProviderConfig(company="Terakeet", board_id="terakeet", careers_page="https://careers.terakeet.com/openings/")
        ),
        GreenhouseProvider(
            ProviderConfig(company="Aledade", board_id="aledade", careers_page="https://aledade.com/current-opportunities")
        ),
        AshbyProvider(ProviderConfig(company="Virta Health", board_id="virtahealth", careers_page="https://jobs.ashbyhq.com/virtahealth")),
        AshbyProvider(ProviderConfig(company="Humata Health", board_id="humatahealth", careers_page="https://jobs.ashbyhq.com/humatahealth")),
        WorkdayProvider(
            ProviderConfig(company="Cityblock Health", board_id=None, careers_page="https://cityblockhealth.wd1.myworkdayjobs.com/en-US/CityblockExternalCareerSite"),
            tenant="cityblockhealth",
            site="CityblockExternalCareerSite",
        ),
        WorkdayProvider(
            ProviderConfig(company="Teladoc Health", board_id=None, careers_page="https://teladoc.wd503.myworkdayjobs.com/en-US/teladochealth_is_hiring"),
            tenant="teladoc",
            site="teladochealth_is_hiring",
        ),
        SimpleHTMLProvider(
            ProviderConfig(company="Deloitte", board_id=None, careers_page="https://apply.deloitte.com/en_US/careers"),
            search_url_template="https://apply.deloitte.com/en_US/careers/SearchJobs/?k={query}",
        ),
        SimpleHTMLProvider(
            ProviderConfig(company="GDIT", board_id=None, careers_page="https://www.gdit.com/careers/"),
            search_url_template="https://www.gdit.com/careers/search?keyword={query}",
        ),
        SimpleHTMLProvider(ProviderConfig(company="Waystar", board_id=None, careers_page="https://careers.waystar.com/jobs/")),
        SimpleHTMLProvider(
            ProviderConfig(company="UnitedHealth Group", board_id=None, careers_page="https://careers.unitedhealthgroup.com/job-search-results/"),
            search_url_template="https://careers.unitedhealthgroup.com/job-search-results/?keywords={query}",
        ),
        SimpleHTMLProvider(
            ProviderConfig(company="Cardinal Health", board_id=None, careers_page="https://jobs.cardinalhealth.com/search/searchjobs?categoryid=901ae6ca-91a9-403a-9402-bc2fbc705e2b"),
            search_url_template="https://jobs.cardinalhealth.com/search/searchjobs?keywords={query}",
        ),
        SimpleHTMLProvider(
            ProviderConfig(company="Adobe", board_id=None, careers_page="https://careers.adobe.com/us/en"),
            search_url_template="https://careers.adobe.com/us/en/search-results?keywords={query}",
        ),
        SimpleHTMLProvider(ProviderConfig(company="Pomelo Care", board_id=None, careers_page="https://www.pomelocare.com/careers")),
        SimpleHTMLProvider(
            ProviderConfig(company="Microsoft", board_id=None, careers_page="https://careers.microsoft.com/v2/global/en/home.html"),
            search_url_template="https://careers.microsoft.com/us/en/search-results?keywords={query}",
        ),
        SimpleHTMLProvider(
            ProviderConfig(company="Booz Allen", board_id=None, careers_page="https://careers.boozallen.com/jobs/search"),
            search_url_template="https://careers.boozallen.com/jobs/search?keywords={query}",
        ),
        SimpleHTMLProvider(
            ProviderConfig(company="Oracle", board_id=None, careers_page="https://careers.oracle.com/en/sites/jobsearch/jobs?location=United%20States&locationId=300000000149325"),
            search_url_template="https://careers.oracle.com/en/sites/jobsearch/jobs?keywords={query}",
        ),
        SimpleHTMLProvider(
            ProviderConfig(company="Humana", board_id=None, careers_page="https://careers.humana.com/us/en"),
            search_url_template="https://careers.humana.com/us/en/search-results?keywords={query}",
        ),
        SimpleHTMLProvider(ProviderConfig(company="Truveta", board_id=None, careers_page="https://www.truveta.com/careers")),
        SimpleHTMLProvider(
            ProviderConfig(company="Oscar Health", board_id=None, careers_page="https://www.hioscar.com/careers/search"),
            search_url_template="https://www.hioscar.com/careers/search?keyword={query}",
        ),
        SimpleHTMLProvider(
            ProviderConfig(company="Accenture", board_id=None, careers_page="https://www.accenture.com/us-en/careers/jobsearch"),
            search_url_template="https://www.accenture.com/us-en/careers/jobsearch?keyword={query}",
        ),
        SimpleHTMLProvider(ProviderConfig(company="Itiliti Health", board_id=None, careers_page="https://www.itilitihealth.com/careers")),
        SimpleHTMLProvider(ProviderConfig(company="Myndshft", board_id=None, careers_page="https://www.myndshft.com/careers/#careers")),
        SimpleHTMLProvider(
            ProviderConfig(company="CoverMyMeds", board_id=None, careers_page="https://careers.mckesson.com/en/search-jobs/CoverMyMeds/733/1"),
            search_url_template="https://careers.mckesson.com/en/search-jobs/CoverMyMeds/733/1?keywords={query}",
        ),
        SimpleHTMLProvider(
            ProviderConfig(company="LinkedIn", board_id=None, careers_page="https://www.linkedin.com/jobs/"),
            search_url_template="https://www.linkedin.com/jobs/search/?keywords={query}",
        ),
    ]


class ScraperSource(BaseJobSource):
    name = "scraper"

    def __init__(self, providers: Optional[List[BaseProvider]] = None):
        self.providers = providers or default_providers()

    def search(self, query: str, limit: int = 50) -> List[Job]:  # pragma: no cover - network
        keywords = keywords_from_query(query)
        results: List[Job] = []
        seen_urls: set[str] = set()
        for provider in self.providers:
            if len(results) >= limit:
                break
            remaining = limit - len(results)
            try:
                postings = provider.fetch_jobs(keywords, limit=remaining)
            except Exception as exc:
                logger.warning("Scraper provider %s failed: %s", provider.company, exc)
                continue
            for posting in postings:
                if len(results) >= limit:
                    break
                if posting.url in seen_urls:
                    continue
                seen_urls.add(posting.url)
                job_id = stable_job_id(posting.title, posting.company, posting.location, posting.url)
                results.append(
                    Job(
                job_id=str(job_id),
                title=posting.title,
                company=posting.company,
                location=posting.location or None,
                url=posting.url,
                source=f"{self.name}:{getattr(provider, 'provider', '')}",
                posted_at=datetime.utcnow().isoformat(),
                description=strip_html(posting.description),
                    )
                )
        return results
