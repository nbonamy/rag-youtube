CREATE TABLE IF NOT EXISTS `runs` (
  `id` varchar(32) NOT NULL PRIMARY KEY,
  `type` varchar(128) NOT NULL,
  `created_at` datetime NOT NULL,
  `total_time` int(11) NOT NULL,
  `input_tokens` int(11) NOT NULL,
  `output_tokens` int(11) NOT NULL,
  `trace` blob NOT NULL
);

CREATE INDEX `runs_created_at` ON `runs`(`created_at`);
CREATE INDEX `runs_type` ON `runs`(`type`);
