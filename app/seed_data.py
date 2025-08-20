from .database import get_connection, init_db
from .repository import PaperRepository
from .models import Paper


def seed() -> None:
	conn = get_connection()
	init_db(conn)
	repo = PaperRepository(conn)

	papers = [
		Paper(
			id=None,
			title="Deep Learning for Image Recognition",
			authors="Alice Smith; Bob Lee",
			year=2020,
			abstract="We evaluate CNN architectures for image classification in resource-constrained settings.",
			department="Computer Science",
			paper_type="Journal",
			research_domain="Computer Vision",
			publisher="Journal of AI Research",
			student="John Doe",
			review_status="Accepted",
			file_path="data/papers/sample1.pdf",
		),
		Paper(
			id=None,
			title="Natural Language Processing for Academic Search",
			authors="Carol Kim",
			year=2021,
			abstract="We present a TF-IDF and BERT-based approach for academic search ranking.",
			department="Information Science",
			paper_type="Conference",
			research_domain="NLP",
			publisher="ACL",
			student="Jane Roe",
			review_status="Under Review",
			file_path="data/papers/sample2.pdf",
		),
	]

	for p in papers:
		try:
			repo.add_paper(p)
		except Exception:
			pass

	conn.close()


if __name__ == "__main__":
	seed() 