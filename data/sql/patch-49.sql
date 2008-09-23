-- #3780: Tabela city location contem entradas duplicadas

SELECT new_cl.min_id as new_id, c.id as old_id INTO alternative
-- elegemos um dos ids para ser unico, poderia ser MAX
  FROM (SELECT MIN(id) as min_id, country, city, state
          FROM city_location
      GROUP BY country, city, state) AS new_cl
-- fazemos o join usando (cidade, estado, pais)
  JOIN city_location c
        ON (LOWER(new_cl.city) = LOWER(c.city) AND
            LOWER(new_cl.country) = LOWER(c.country) AND
            LOWER(new_cl.state) = LOWER(c.state))
-- ignoramos as entraras que nao mudariam
 WHERE new_cl.min_id != c.id;

-- remove as referencias invalidas
UPDATE address
   SET city_location_id = alternative.new_id
  FROM alternative
 WHERE city_location_id = alternative.old_id;

UPDATE person_adapt_to_individual
   SET birth_location_id = alternative.new_id
  FROM alternative
 WHERE birth_location_id = alternative.old_id;

-- remove as entradas duplicadas
DELETE FROM city_location WHERE id IN (SELECT old_id FROM alternative);

-- adiciona restricao
ALTER TABLE city_location ADD UNIQUE(country, state, city);

-- remove as tabelas usadas temporariamente
DROP TABLE alternative;
