-- FIG schema. Generated from app/models.py -- regenerate rather than
-- hand-editing, or the two drift apart.
--
-- You do not need to run this: app.db.init_db() calls create_all() on boot,
-- against whatever DATABASE_URL points at. This file is here for review, and
-- for running by hand in the Supabase SQL editor if you prefer.
--
--   python scripts/dump_schema.py > supabase_schema.sql


CREATE TABLE IF NOT EXISTS accounts (
	id VARCHAR NOT NULL, 
	name VARCHAR NOT NULL, 
	slug VARCHAR NOT NULL, 
	kind VARCHAR NOT NULL, 
	contact_email VARCHAR, 
	white_label BOOLEAN NOT NULL, 
	brand_name VARCHAR, 
	brand_color VARCHAR, 
	site_floor INTEGER NOT NULL, 
	rate_override_cents INTEGER, 
	stripe_customer_id VARCHAR, 
	stripe_subscription_id VARCHAR, 
	created_at TIMESTAMP WITHOUT TIME ZONE, 
	PRIMARY KEY (id)
);

CREATE UNIQUE INDEX IF NOT EXISTS ix_accounts_slug ON accounts (slug);

CREATE TABLE IF NOT EXISTS jobs (
	id VARCHAR NOT NULL, 
	kind VARCHAR NOT NULL, 
	payload JSON NOT NULL, 
	status VARCHAR NOT NULL, 
	attempts INTEGER NOT NULL, 
	max_attempts INTEGER NOT NULL, 
	error TEXT, 
	run_after TIMESTAMP WITHOUT TIME ZONE, 
	claimed_at TIMESTAMP WITHOUT TIME ZONE, 
	finished_at TIMESTAMP WITHOUT TIME ZONE, 
	created_at TIMESTAMP WITHOUT TIME ZONE, 
	PRIMARY KEY (id)
);

CREATE INDEX IF NOT EXISTS ix_jobs_status ON jobs (status);

CREATE INDEX IF NOT EXISTS ix_jobs_run_after ON jobs (run_after);

CREATE TABLE IF NOT EXISTS api_keys (
	id VARCHAR NOT NULL, 
	account_id VARCHAR NOT NULL, 
	label VARCHAR NOT NULL, 
	prefix VARCHAR NOT NULL, 
	key_hash VARCHAR NOT NULL, 
	last_used_at TIMESTAMP WITHOUT TIME ZONE, 
	revoked BOOLEAN NOT NULL, 
	created_at TIMESTAMP WITHOUT TIME ZONE, 
	PRIMARY KEY (id), 
	FOREIGN KEY(account_id) REFERENCES accounts (id)
);

CREATE INDEX IF NOT EXISTS ix_api_keys_account_id ON api_keys (account_id);

CREATE INDEX IF NOT EXISTS ix_api_keys_prefix ON api_keys (prefix);

CREATE TABLE IF NOT EXISTS sites (
	id VARCHAR NOT NULL, 
	account_id VARCHAR NOT NULL, 
	hostname VARCHAR NOT NULL, 
	label VARCHAR, 
	client_name VARCHAR, 
	is_active BOOLEAN NOT NULL, 
	monitor BOOLEAN NOT NULL, 
	monitor_days INTEGER NOT NULL, 
	is_verified BOOLEAN NOT NULL, 
	verification_token VARCHAR, 
	verification_method VARCHAR, 
	verified_at TIMESTAMP WITHOUT TIME ZONE, 
	last_scanned_at TIMESTAMP WITHOUT TIME ZONE, 
	created_at TIMESTAMP WITHOUT TIME ZONE, 
	PRIMARY KEY (id), 
	CONSTRAINT uq_site_account_hostname UNIQUE (account_id, hostname), 
	FOREIGN KEY(account_id) REFERENCES accounts (id)
);

CREATE INDEX IF NOT EXISTS ix_sites_hostname ON sites (hostname);

CREATE INDEX IF NOT EXISTS ix_sites_account_id ON sites (account_id);

CREATE TABLE IF NOT EXISTS users (
	id VARCHAR NOT NULL, 
	account_id VARCHAR, 
	email VARCHAR NOT NULL, 
	supabase_uid VARCHAR, 
	role VARCHAR NOT NULL, 
	created_at TIMESTAMP WITHOUT TIME ZONE, 
	PRIMARY KEY (id), 
	FOREIGN KEY(account_id) REFERENCES accounts (id), 
	UNIQUE (email), 
	UNIQUE (supabase_uid)
);

CREATE INDEX IF NOT EXISTS ix_users_account_id ON users (account_id);

CREATE TABLE IF NOT EXISTS scans (
	id VARCHAR NOT NULL, 
	site_id VARCHAR NOT NULL, 
	status VARCHAR NOT NULL, 
	trigger VARCHAR NOT NULL, 
	error TEXT, 
	pages_crawled INTEGER NOT NULL, 
	pages_requested INTEGER NOT NULL, 
	score INTEGER, 
	score_craft INTEGER, 
	score_structure INTEGER, 
	score_search INTEGER, 
	score_answers INTEGER, 
	started_at TIMESTAMP WITHOUT TIME ZONE, 
	finished_at TIMESTAMP WITHOUT TIME ZONE, 
	created_at TIMESTAMP WITHOUT TIME ZONE, 
	PRIMARY KEY (id), 
	FOREIGN KEY(site_id) REFERENCES sites (id)
);

CREATE INDEX IF NOT EXISTS ix_scans_site_id ON scans (site_id);

CREATE TABLE IF NOT EXISTS findings (
	id VARCHAR NOT NULL, 
	scan_id VARCHAR NOT NULL, 
	page_url VARCHAR, 
	"check" VARCHAR NOT NULL, 
	layer VARCHAR NOT NULL, 
	severity VARCHAR NOT NULL, 
	weight FLOAT NOT NULL, 
	summary TEXT NOT NULL, 
	why TEXT, 
	fix TEXT, 
	evidence JSON, 
	count INTEGER NOT NULL, 
	ai_written BOOLEAN NOT NULL, 
	created_at TIMESTAMP WITHOUT TIME ZONE, 
	PRIMARY KEY (id), 
	FOREIGN KEY(scan_id) REFERENCES scans (id)
);

CREATE INDEX IF NOT EXISTS ix_findings_scan_id ON findings (scan_id);

CREATE INDEX IF NOT EXISTS ix_findings_check ON findings ("check");

CREATE TABLE IF NOT EXISTS pages (
	id VARCHAR NOT NULL, 
	scan_id VARCHAR NOT NULL, 
	url VARCHAR NOT NULL, 
	path VARCHAR NOT NULL, 
	title VARCHAR, 
	status_code INTEGER, 
	word_count INTEGER NOT NULL, 
	section_roles JSON, 
	fetched_at TIMESTAMP WITHOUT TIME ZONE, 
	PRIMARY KEY (id), 
	FOREIGN KEY(scan_id) REFERENCES scans (id)
);

CREATE INDEX IF NOT EXISTS ix_pages_scan_id ON pages (scan_id);
