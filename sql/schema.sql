-- Drop tables if they exist (for clean re-runs)
DROP TABLE IF EXISTS relationships;
DROP TABLE IF EXISTS patents;
DROP TABLE IF EXISTS inventors;
DROP TABLE IF EXISTS companies;

-- Patents table
CREATE TABLE patents (
    patent_id VARCHAR(36) PRIMARY KEY,
    title TEXT,
    abstract TEXT,
    filing_date DATE,
    year INTEGER
);

-- Inventors table
CREATE TABLE inventors (
    inventor_id VARCHAR(128) PRIMARY KEY,
    name VARCHAR(255),
    country VARCHAR(16)
);

-- Companies (assignees) table
CREATE TABLE companies (
    company_id VARCHAR(128) PRIMARY KEY,
    name VARCHAR(255)
);

-- Relationships table (junction table)
CREATE TABLE relationships (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    patent_id VARCHAR(36),
    inventor_id VARCHAR(128),
    company_id VARCHAR(128),
    FOREIGN KEY (patent_id) REFERENCES patents(patent_id),
    FOREIGN KEY (inventor_id) REFERENCES inventors(inventor_id),
    FOREIGN KEY (company_id) REFERENCES companies(company_id)
);

-- Indexes for faster queries
CREATE INDEX idx_rel_patent ON relationships(patent_id);
CREATE INDEX idx_rel_inventor ON relationships(inventor_id);
CREATE INDEX idx_rel_company ON relationships(company_id);
CREATE INDEX idx_patents_year ON patents(year);