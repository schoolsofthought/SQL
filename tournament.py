#!/usr/bin/env python
# 
# tournament.py -- implementation of a Swiss-system tournament
#

import psycopg2
import bleach
import random


def connect():
    """Connect to the PostgreSQL database.  Returns a database connection."""
    return psycopg2.connect("dbname=tournament")


def deleteMatches():
    """Remove all the match records from the database."""
    db = connect()
    c = db.cursor()
    c.execute("TRUNCATE matchups")
    c.execute("UPDATE scorecard SET (win, loss) = (0, 0)")
    db.commit()
    db.close()

def deletePlayers():
    """Remove all the player records from the database."""
    db = connect()
    c = db.cursor()
    c.execute("TRUNCATE scorecard, roster")
    db.commit()
    db.close()

def countPlayers():
    """Returns the number of players currently registered."""
    db = connect()
    c = db.cursor()
    c.execute("SELECT COUNT(*) FROM roster")
    return int(c.fetchall()[0][0])
    db.close()

def registerPlayer(name):
    """Adds a player to the tournament database.
  
    The database assigns a unique serial id number for the player.  (This
    should be handled by your SQL database schema, not in your Python code.)
  
    Args:
      name: the player's full name (need not be unique).
    """
    db = connect()
    c = db.cursor()
    c.execute("INSERT INTO roster (player) VALUES (%s)", (bleach.clean(name),))
    c.execute("SELECT id FROM roster WHERE player = %s", (bleach.clean(name),))
    id = c.fetchall()[0][0]
    c.execute("INSERT INTO scorecard (id, win, loss) values (%s, 0, 0)", (id,))
    db.commit()
    db.close()

def playerStandings():
    """Returns a list of the players and their win records, sorted by wins.

    The first entry in the list should be the player in first place, or a player
    tied for first place if there is currently a tie.

    Returns:
      A list of tuples, each of which contains (id, name, wins, matches):
        id: the player's unique id (assigned by the database)
        name: the player's full name (as registered)
        wins: the number of matches the player has won
        matches: the number of matches the player has played
    """
    db = connect()
    c = db.cursor()
    c.execute("SELECT scorecard.id, roster.player, scorecard.win, (scorecard.win + scorecard.loss) AS matches  FROM scorecard, roster WHERE scorecard.id = roster.id ORDER BY scorecard.win DESC")
    standings = c.fetchall()
    if len(standings) == 0:
      c.execute("SELECT * FROM roster;")
      standings = c.fetchall()
    db.close()
    return standings

def reportMatch(winner, loser):
    """Records the outcome of a single match between two players.

    Args:
      winner:  the id number of the player who won
      loser:  the id number of the player who lost
    """
    db = connect()
    c = db.cursor()
    c.execute("INSERT INTO scorecard (id, win, loss) values (%s, 1, 0) ON CONFLICT (id) DO UPDATE SET win = scorecard.win + 1", (winner,))
    c.execute("INSERT INTO scorecard (id, win, loss) values (%s, 0,1) ON CONFLICT (id) DO UPDATE SET loss = scorecard.loss + 1", (loser,))

    db.commit()
    db.close()

def fill_roster():
    players = ['John Wall', 'Steph Curry', 'James Johnson', 'Lebron James', 'James Harden', 'James Johnson', 'Kobe Bryant', 'Shaq']
    for i in players:
      registerPlayer(i)

def reset_id():
    db = connect()
    c = db.cursor()
    c.execute("ALTER SEQUENCE roster_id_seq RESTART WITH 1;")
    c.execute("UPDATE roster SET id = nextval('roster_id_seq');")
    db.commit()
    db.close()   

def view_roster():
    db = connect()
    c = db.cursor()
    c.execute("SELECT * FROM roster;")
    print c.fetchall()
    db.close()
 
def swissPairings():
    """Returns a list of pairs of players for the next round of a match.
  
    Assuming that there are an even number of players registered, each player
    appears exactly once in the pairings.  Each player is paired with another
    player with an equal or nearly-equal win record, that is, a player adjacent
    to him or her in the standings.
  
    Returns:
      A list of tuples, each of which contains (id1, name1, id2, name2)
        id1: the first player's unique id
        name1: the first player's name
        id2: the second player's unique id
        name2: the second player's name
    """
    db = connect()
    c = db.cursor()
    c.execute("SELECT * FROM roster;")
    roster = c.fetchall()
    matchup_list = []

    if len(roster) == 0:
      fill_roster()
      c.execute("SELECT * FROM roster;")
      roster = c.fetchall()

    standings = playerStandings()
    c.execute("SELECT * FROM matchups;")
    

    if len(c.fetchall()) == 0:
      round = 1
      for i in xrange(0,len(roster),2):
        c.execute(
        "INSERT INTO matchups (round, id1, id2) VALUES (%s, %s, %s);", 
        (round, roster[i][0], roster[i+1][0],))
        matchup_list.append(match_player_id(roster[i][0], roster[i+1][0], c))
    else:
      c.execute("SELECT max(round) from matchups;")
      round = 1 + c.fetchall()[0][0]
      '''QUERY = 
	SELECT DISTINCT ON (id2) *  
	  FROM (
	    SELECT DISTINCT ON (id1) * 
               FROM (SELECT a.id AS id1, b.id AS id2, a.win AS wins, a.loss AS losses 
                 FROM scorecard AS a 
                   JOIN scorecard AS b 
                     ON a.win = b.win AND a.loss = b.loss) AS foo 
                        WHERE id1 < id2) AS bar;

      '''
      QUERY = "SELECT * FROM scorecard ORDER BY win DESC, loss ASC;"
      c.execute(QUERY)
      nextround = c.fetchall()
      for i in xrange(0,len(nextround),2):
        id1 = nextround[i][0]
        id2 = nextround[i+1][0]
        c.execute(
        "INSERT INTO matchups (round, id1, id2) VALUES (%s, %s, %s);", 
        (round, id1, id2,))  
        matchup_list.append(match_player_id(id1, id2, c))
    db.commit()
    pick_a_winner(round)
    db.close()
    return matchup_list

def match_player_id(id1, id2, db_cursor):
    db_cursor.execute("SELECT player FROM roster WHERE id IN (%s, %s)", (id1,id2,))
    players = db_cursor.fetchall()
    return [id1, players[0][0], id2, players[1][0]]

def pick_a_winner(round):
    db = connect()
    c = db.cursor()
    c.execute("SELECT * FROM matchups WHERE matchups.round = %s;", (round,))
    matchups = c.fetchall()
    db.close()
    for match in matchups:
	result = random.randint(1,2)
        winner = match[result]        
        loser = match[len(match)-result]
        reportMatch(winner, loser)

if __name__ == "__main__":
  a = swissPairings()
  print a

