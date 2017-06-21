-- Table definitions for the tournament project.
--
-- Put your SQL 'create table' statements in this file; also 'create view'
-- statements if you choose to use it.
--
-- You can write comments in this file by starting them with two dashes, like
-- these lines here.

CREATE DATABASE tournament;

\c tournament;

CREATE TABLE roster (id serial primary key, player text not null);

CREATE TABLE matchups(round int not null, id1 int not null, id2 int not null, primary key (round, id1, id2));

CREATE TABLE scorecard(id int references roster, win int not null, loss int not null, unique(id));



