
import json
import sqlite3

# CREATE TABLE IF NOT EXISTS `runs` (
#   `id` varchar(32) NOT NULL PRIMARY KEY,
#   `type` varchar(128) NOT NULL,
#   `created_at` datetime NOT NULL,
#   `total_time` int(11) NOT NULL,
#   `input_tokens` int(11) NOT NULL,
#   `output_tokens` int(11) NOT NULL,
#   `trace` blob NOT NULL
# );

class Database:

  def __init__(self, config):
    self.config = config
    self.con = sqlite3.connect(config.database_path())

  def get_runs(self):
    cursor = self.con.cursor()
    cursor.execute("SELECT * FROM runs ORDER BY created_at DESC")
    return [ {
      'id': run[0],
      'type': run[1],
      'created_at': run[2],
      'total_time': run[3],
      'input_tokens': run[4],
      'output_tokens': run[5],
      'trace': json.loads(run[6])
    } for run in cursor.fetchall() ]

  def add_run(self, run, type):
    cursor = self.con.cursor()
    row=(
      run['chain']['id'],
      type,
      run['chain']['created_at'],
      run['performance']['total_time'],
      run['performance']['input_tokens'],
      run['performance']['output_tokens'],
      json.dumps(run)
    )
    cursor.execute("INSERT INTO runs VALUES (?, ?, ?, ?, ?, ?, ?)", row)
    self.con.commit()
  
  def delete_run(self, id):
    cursor = self.con.cursor()
    cursor.execute("DELETE FROM runs WHERE id=?", (id,))
    self.con.commit()
    