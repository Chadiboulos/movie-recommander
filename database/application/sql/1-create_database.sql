CREATE TABLE IF NOT EXISTS genre (
	genreid serial4 NOT NULL,
	"name" varchar NOT NULL,
	CONSTRAINT genre_pkey PRIMARY KEY (genreid)
);

CREATE TABLE IF NOT EXISTS  movie (
	movieid serial4 NOT NULL,
	title varchar NOT NULL,
	imdbid int4 NULL,
	tmdbid int4 NULL,
	"year" int4 NULL,
	decade int4 NULL,
	CONSTRAINT movie_pkey PRIMARY KEY (movieid)
);
CREATE TABLE IF NOT EXISTS imdb_data (
	movieid int4 NOT NULL,
	titre varchar(255) NULL,
	summary text NULL,
	certificat varchar(50) NULL,
	duration varchar(10) NULL,
	poster text NULL,
	directors varchar(500) NULL,
	writers varchar(500) NULL,
	stars varchar(500) NULL,
	CONSTRAINT imdb_data_pkey PRIMARY KEY (movieid)
);
CREATE INDEX movie_decade_idx ON movie USING btree (decade);
CREATE INDEX movie_year_idx ON movie USING btree (year);
CREATE TABLE IF NOT EXISTS model_prediction (
	modelid serial4 NOT NULL,
	class_name varchar NULL,
	params varchar NULL,
	mlflow_run_id varchar NULL,
	mlflow_experiment_name varchar NULL,
	start_date timestamp NOT NULL,
	end_date timestamp NULL,
	CONSTRAINT model_prediction_pkey PRIMARY KEY (modelid)
);
CREATE TABLE IF NOT EXISTS movie_genre (
	movieid int4 NOT NULL,
	genreid int4 NOT NULL,
	CONSTRAINT movie_genre_pkey PRIMARY KEY (movieid, genreid),
	CONSTRAINT movie_genre_genreid_fkey FOREIGN KEY (genreid) REFERENCES genre(genreid),
	CONSTRAINT movie_genre_movieid_fkey FOREIGN KEY (movieid) REFERENCES movie(movieid)
);
CREATE INDEX movie_genre_movieid_idx ON movie_genre USING btree (movieid);
CREATE TABLE IF NOT EXISTS users (
	userid serial4 NOT NULL,
	username varchar NOT NULL,
	"password" varchar NOT NULL,
	is_admin bool DEFAULT false NULL,
	CONSTRAINT username_unique UNIQUE (username),
	CONSTRAINT users_pk PRIMARY KEY (userid)
);
CREATE TABLE IF NOT EXISTS rating (
	userid int4 NOT NULL,
	movieid int4 NOT NULL,
	rating float8 NOT NULL,
	"timestamp" int4 NOT NULL,
	CONSTRAINT rating_pkey PRIMARY KEY (userid, movieid),
	CONSTRAINT rating_movieid_fkey FOREIGN KEY (movieid) REFERENCES movie(movieid)
);
CREATE INDEX rating_movieid_idx ON rating USING btree (movieid);
CREATE INDEX rating_timestamp_idx ON rating USING btree ("timestamp");
CREATE MATERIALIZED VIEW table_recap_view
TABLESPACE pg_default
AS SELECT m.movieid,
    m.title,
    m.decade,
    m.year,
    string_agg(DISTINCT g.name::text, '|'::text) AS genre,
    avg(r.rating) AS avg_rating,
    count(r.rating) AS nb_rating
   FROM movie m
     JOIN movie_genre mg ON m.movieid = mg.movieid
     JOIN genre g ON g.genreid = mg.genreid
     JOIN rating r ON r.movieid = m.movieid
  GROUP BY m.movieid
 HAVING avg(r.rating) > 2.5::double precision AND count(r.rating) > 100
WITH DATA;
CREATE INDEX table_recap_view_avg_rating_idx ON table_recap_view USING btree (avg_rating);
CREATE INDEX table_recap_view_decade_idx ON table_recap_view USING btree (decade);
CREATE INDEX table_recap_view_year_idx ON table_recap_view USING btree (year);