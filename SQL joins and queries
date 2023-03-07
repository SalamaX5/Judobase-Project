-- join tables for player comparison analysis

SELECT p.player_id, p.player_name, p.nationality, w.weight, c.comp_name, c.start_date, c.comp_id, m.match_id, m.player1_id, m.player2_id, m.round, m.winner_id,
SPLIT_PART(md.event,':',1) as score,
SPLIT_PART(SPLIT_PART(md.event,':',2),'/',1) as score_type,
SPLIT_PART(SPLIT_PART(md.event,':',2),'/',2) as technique_or_reason,
md.time
FROM matches m
INNER JOIN competitions c ON c.comp_id = m.comp_id
INNER JOIN players p ON p.player_id = m.player1_id OR p.player_id = m.player2_id
LEFT JOIN match_details md ON md.player_id = p.player_id AND m.match_id = md.match_id AND m.comp_id = md.comp_id
INNER JOIN weights w ON w.player_id = p.player_id
WHERE c.start_date BETWEEN w.start_date AND w.end_date 
	OR c.start_date >= w.start_date AND w.end_date IS NULL
ORDER BY p.player_id, c.comp_id



-- join tables for score analysis

SELECT c.comp_id, c.comp_name, m.match_id, m.player1_id, m.player2_id, m.round, m.winner_id,
SPLIT_PART(md.event,':',1) as score,
SPLIT_PART(SPLIT_PART(md.event,':',2),'/',1) as score_type,
SPLIT_PART(SPLIT_PART(md.event,':',2),'/',2) as technique_or_reason,
md.time, p.player_name, p.nationality, w.weight
FROM matches m
INNER JOIN competitions c ON c.comp_id = m.comp_id
INNER JOIN players p ON p.player_id = m.player1_id OR p.player_id = m.player2_id
INNER JOIN match_details md ON md.match_id = m.match_id AND md.comp_id = m.comp_id AND md.player_id = p.player_id
INNER JOIN weights w on w.player_id = p.player_id
WHERE c.start_date BETWEEN w.start_date AND w.end_date 
	OR c.start_date >= w.start_date AND w.end_date IS NULL
ORDER BY c.comp_id




--queries/exploratory data analysis

-- 1) Who is the US player with most Wins in a Grand Slam in 2019?
	-- Result set: athlete_name, total number of wins

SELECT p.player_name, count(m.winner_id)
from matches m
inner join players p on m.winner_id = p.player_id
inner join competitions c on m.comp_id = c.comp_id
where p.nationality = 'United States of America' and c.start_date between '2019-01-01' and '2019-12-31'
and c.comp_name like '%Grand Slam%'
group by p.player_name
order by count(m.winner_id) desc


-- 2) Which US player had the most Shidos in 2019?
	-- Result set: athlete_name, total number of shidos

SELECT p.player_name, count(md.event)
from match_details md
inner join players p on md.player_id = p.player_id
inner join competitions c on md.comp_id = c.comp_id
where p.nationality = 'United States of America' and
c.start_date between '2019-01-01' and '2019-12-31' and
md.event like '%Shido%' and md.event not like '%Cancel%'
group by p.player_name
order by count(md.event) desc


-- 3) Which country had the most wins throughout the olympic qualifying period broken up by year?

SELECT DISTINCT ON (t.year) t.year, t.country, MAX(wins)
FROM (SELECT EXTRACT(year FROM c.start_date) AS year, p.nationality AS country, COUNT(m.winner_id) AS wins
FROM matches m
INNER JOIN players p ON m.winner_id = p.player_id
INNER JOIN competitions c ON m.comp_id = c.comp_id
GROUP BY year, country
ORDER BY year DESC, COUNT(m.winner_id) DESC) AS t
GROUP BY t.year, t.country
ORDER BY t.year, MAX(wins) DESC

-- 4) Which competition had the most number of medals for a given country?

SELECT c.comp_name,
p.nationality,
(COUNT(CASE WHEN p.player_id = m.winner_id AND m.round = 'Final' THEN 1 END) +
COUNT(CASE WHEN p.player_id <> m.winner_id AND m.round = 'Final' THEN 1 END) +
COUNT(CASE WHEN p.player_id = m.winner_id AND m.round = 'Bronze' THEN 1 END)) AS medals,
COUNT(CASE WHEN p.player_id = m.winner_id AND m.round = 'Final' THEN 1 END) AS golds,
COUNT(CASE WHEN p.player_id <> m.winner_id AND m.round = 'Final' THEN 1 END) AS silvers,
COUNT(CASE WHEN p.player_id = m.winner_id AND m.round = 'Bronze' THEN 1 END) AS bronzes
FROM matches m
INNER JOIN competitions c ON c.comp_id = m.comp_id
INNER JOIN players p ON p.player_id = m.winner_id OR p.player_id = m.player1_id OR p.player_id = m.player2_id
GROUP BY c.comp_name, p.nationality
ORDER BY medals DESC, golds DESC, silvers DESC, bronzes DESC LIMIT 1

-- 5) Who are the top 3 competitors, by weight class, at the end of the olympic qualification period?

SELECT * FROM
(
SELECT w.weight, p.player_name, COUNT(m.winner_ID),
	ROW_NUMBER() OVER (PARTITION BY w.weight ORDER BY COUNT(m.winner_id) DESC) AS w_rank
FROM matches m
INNER JOIN weights w ON m.winner_id = w.player_id
INNER JOIN competitions c ON m.comp_id = c.comp_id
INNER JOIN players p ON m.winner_id = p.player_id
WHERE c.start_date BETWEEN w.start_date AND w.end_date 
	OR c.start_date >= w.start_date AND w.end_date IS NULL
GROUP BY w.weight, p.player_name
ORDER BY w.weight, COUNT(m.winner_id) DESC) AS rank
WHERE w_rank <= 3

-- 6) What is the record for each US athlete during the Olympic qualification period? 

SELECT p.player_name,
COUNT(CASE WHEN p.player_id = m.winner_id THEN 1 END) AS w,
COUNT(CASE WHEN p.player_id <> m.winner_id THEN 1 END) AS l
FROM matches m
INNER JOIN players p ON p.player_id = m.winner_id
OR p.player_id = m.player1_id
OR p.player_id = m.player2_id
WHERE p.nationality = 'United States of America'
GROUP BY p.player_name
ORDER BY w DESC, l DESC

-- 7) What is the longest time a competitor went without competing during the Olympic qualification period? How did that affect their performance post return? 

WITH cte AS
	(
	SELECT p.player_id, p.player_name, c.comp_name, c.start_date,
	LEAD(c.start_date) OVER(PARTITION BY p.player_id ORDER by p.player_id) - c.start_date as days_gap 
	FROM matches m
	INNER JOIN players p ON p.player_id = m.player1_id OR p.player_id = m.player2_id
	INNER JOIN competitions c ON c.comp_id = m.comp_id
	GROUP BY p.player_id, p.player_name, c.start_date, c.comp_name
	ORDER BY days_gap DESC NULLS LAST
	LIMIT 1
	)
SELECT cte.player_id, cte.player_name, cte.days_gap,
COUNT(CASE WHEN cte.player_id = m.winner_id THEN 1 END) AS w,
COUNT(CASE WHEN cte.player_id <> m.winner_id THEN 1 END) AS l
FROM matches m
INNER JOIN cte ON cte.player_id = m.winner_id
OR cte.player_id = m.player1_id
OR cte.player_id = m.player2_id
INNER JOIN competitions c ON m.comp_id = c.comp_id
WHERE c.start_date > cte.start_date
GROUP BY cte.player_id, cte.player_name, cte.days_gap



-- *** CTE in a CTE

WITH player_gap AS
	(
	SELECT p.player_id, p.player_name, c.comp_name, c.start_date,
	LEAD(c.start_date) OVER(PARTITION BY p.player_id ORDER by p.player_id) - c.start_date as days_gap 
	FROM matches m
	INNER JOIN players p ON p.player_id = m.player1_id OR p.player_id = m.player2_id
	INNER JOIN competitions c ON c.comp_id = m.comp_id
	GROUP BY p.player_id, p.player_name, c.start_date, c.comp_name
	ORDER BY days_gap DESC NULLS LAST
	LIMIT 1
	),
	
return_data as (
SELECT pg.player_id, pg.player_name, pg.days_gap,
COUNT(CASE WHEN pg.player_id = m.winner_id THEN 1 END) AS w,
COUNT(CASE WHEN pg.player_id <> m.winner_id THEN 1 END) AS l
FROM matches m
INNER JOIN player_gap pg ON pg.player_id = m.winner_id
OR pg.player_id = m.player1_id
OR pg.player_id = m.player2_id
INNER JOIN competitions c ON m.comp_id = c.comp_id
WHERE c.start_date > pg.start_date
GROUP BY pg.player_id, pg.player_name, pg.days_gap
	),
	
pre_data as (
SELECT pg.player_id, pg.player_name, pg.days_gap,
COUNT(CASE WHEN pg.player_id = m.winner_id THEN 1 END) AS w,
COUNT(CASE WHEN pg.player_id <> m.winner_id THEN 1 END) AS l
FROM matches m
INNER JOIN player_gap pg ON pg.player_id = m.winner_id
OR pg.player_id = m.player1_id
OR pg.player_id = m.player2_id
INNER JOIN competitions c ON m.comp_id = c.comp_id
WHERE c.start_date <= pg.start_date
GROUP BY pg.player_id, pg.player_name, pg.days_gap
) 

select 
 rd.player_name, 
 rd.days_gap, 
 rd.w as return_w, 
 rd.l as return_l,
 pd.w as pre_w, 
 pd.l as pre_l
from return_data rd
inner join pre_data pd on pd.player_id = rd.player_id
