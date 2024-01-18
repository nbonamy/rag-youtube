
import json
import sqlite3

# CREATE TABLE IF NOT EXISTS `runs` (
#   `id` varchar(32) NOT NULL PRIMARY KEY,
#   `type` varchar(128) NOT NULL,
#   `created_at` datetime NOT NULL,
#   `total_time` int(11) NOT NULL,
#   `input_tokens` int(11) NOT NULL,
#   `output_tokens` int(11) NOT NULL,
#   `trace` blob NOT NULL,
#   'evaluation_crit_trace' blob NOT NULL,
#   `evaluation_qa_trace` blob NOT NULL
# );

class Database:

  def __init__(self, config):
    self.config = config
    self.con = sqlite3.connect(config.database_path())

  def get_runs(self):
    cursor = self.con.cursor()
    cursor.execute("SELECT * FROM runs ORDER BY created_at DESC")
    return [ self.__row_to_run(row) for row in cursor.fetchall() ]

  def get_run(self, id):
    cursor = self.con.cursor()
    cursor.execute("SELECT * FROM runs WHERE id=?", (id,))
    return self.__row_to_run(cursor.fetchone())

  def add_run(self, run, type):
    cursor = self.con.cursor()
    row=(
      run['chain']['id'],
      type,
      run['chain']['created_at'],
      run['performance']['total_time'],
      run['performance']['input_tokens'],
      run['performance']['output_tokens'],
      json.dumps(run),
      None,
      None
    )
    cursor.execute("INSERT INTO runs VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)", row)
    self.con.commit()

  def set_run_eval_crit(self, id, trace):
    cursor = self.con.cursor()
    cursor.execute("UPDATE runs SET evaluation_crit_trace=? WHERE id=?", (json.dumps(trace), id))
    self.con.commit()

  def set_run_eval_qa(self, id, trace):
    cursor = self.con.cursor()
    cursor.execute("UPDATE runs SET evaluation_qa_trace=? WHERE id=?", (json.dumps(trace), id))
    self.con.commit()
  
  def delete_run(self, id):
    cursor = self.con.cursor()
    cursor.execute("DELETE FROM runs WHERE id=?", (id,))
    self.con.commit()
  
  def __row_to_run(self, row):
    return {
      'id': row[0],
      'type': row[1],
      'created_at': row[2],
      'total_time': row[3],
      'input_tokens': row[4],
      'output_tokens': row[5],
      'trace': json.loads(row[6]),
      'evaluation_crit_trace': json.loads(row[7]) if row[7] else None,
      'evaluation_qa_trace': json.loads(row[8]) if row[8] else None
    }    