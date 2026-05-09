-- ============================================
-- PATENT ANALYSIS QUERIES
-- ============================================

-- Q1: Top Inventors - Who has the most patents?
SELECT 
    i.inventor_name,
    COUNT(DISTINCT i.patent_id) AS patent_count
FROM inventors i
GROUP BY i.inventor_id, i.inventor_name
ORDER BY patent_count DESC
LIMIT 10;


-- Q2: Top Companies - Which companies own the most patents?
SELECT 
    a.company_name,
    COUNT(DISTINCT a.patent_id) AS patent_count
FROM assignees a
GROUP BY a.company_id, a.company_name
ORDER BY patent_count DESC
LIMIT 10;


-- Q3: Top Countries - Which countries produce the most patents?
SELECT 
    i.country,
    COUNT(DISTINCT i.patent_id) AS patent_count
FROM inventors i
WHERE i.country IS NOT NULL AND i.country != ''
GROUP BY i.country
ORDER BY patent_count DESC
LIMIT 10;


-- Q4: Trends Over Time - Patents filed each year
SELECT 
    filing_year,
    COUNT(*) AS patent_count
FROM patents
WHERE filing_year IS NOT NULL
GROUP BY filing_year
ORDER BY filing_year;


-- Q5: JOIN Query - Patents with inventors and companies
SELECT 
    p.patent_id,
    p.title,
    p.filing_year,
    i.inventor_name,
    i.country AS inventor_country,
    a.company_name
FROM patents p
LEFT JOIN inventors i ON p.patent_id = i.patent_id
LEFT JOIN assignees a ON p.patent_id = a.patent_id
LIMIT 100;


-- Q6: CTE Query - Inventors who have patents with multiple companies
WITH inventor_company_counts AS (
    SELECT 
        i.inventor_id,
        COUNT(DISTINCT a.company_id) AS company_count,
        COUNT(DISTINCT i.patent_id) AS patent_count
    FROM inventors i
    JOIN assignees a ON i.patent_id = a.patent_id
    GROUP BY i.inventor_id
    HAVING COUNT(DISTINCT a.company_id) > 1
)
SELECT 
    i.inventor_name,
    i.country,
    icc.patent_count,
    icc.company_count
FROM inventor_company_counts icc
JOIN inventors i ON icc.inventor_id = i.inventor_id
ORDER BY icc.patent_count DESC
LIMIT 20;


-- Q7: Ranking Query - Rank inventors using window functions
WITH inventor_patents AS (
    SELECT 
        i.inventor_id,
        i.inventor_name,
        i.country,
        COUNT(DISTINCT i.patent_id) AS patent_count
    FROM inventors i
    GROUP BY i.inventor_id, i.inventor_name, i.country
)
SELECT 
    inventor_name,
    country,
    patent_count,
    RANK() OVER (ORDER BY patent_count DESC) AS world_rank,
    RANK() OVER (PARTITION BY country ORDER BY patent_count DESC) AS country_rank
FROM inventor_patents
ORDER BY patent_count DESC
LIMIT 50;