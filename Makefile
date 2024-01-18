load:
	@-rm -rf db > /dev/null 2>&1
	@-rm loaded.json > /dev/null 2>&1
	./src/document_loader.py

run:
	watchfiles ./src/app.py src rag-youtube.conf

createdb:
	@-rm -f rag-youtube.db > /dev/null 2>&1
	sqlite3 rag-youtube.db < schema.sql

