CREATE TABLE IF NOT EXISTS archive (
  id INTEGER PRIMARY KEY NOT NULL,
  image_path VARCHAR(255),
  thumbnail_path VARCHAR(255),

  CONSTRAINT image_path_unique UNIQUE (image_path),
  CONSTRAINT thumbnail_path_unique UNIQUE (thumbnail_path)
);

-- CREATE TABLE IF NOT EXISTS contributor (
--   contributor_id SERIAL NOT NULL PRIMARY KEY,
--   contributor_key VARCHAR(255),
--   contributor_alias VARCHAR(255),
--   is_allowed BOOLEAN DEFAULT false,

--   CONSTRAINT contributor_key_unique UNIQUE (contributor_key)
-- );

-- CREATE TABLE IF NOT EXISTS tag_def (
--   tag_id SERIAL NOT NULL PRIMARY KEY,
--   tag_description VARCHAR(255),
--   tag_created_by INTEGER,

--   CONSTRAINT tag_description_unique UNIQUE (tag_description),
--   CONSTRAINT tag_created_by_fk FOREIGN KEY (tag_created_by) 
--     REFERENCES contributor (contributor_id) ON DELETE NO ACTION
-- );

-- CREATE TABLE IF NOT EXISTS tag_rel (
--   tag_id INTEGER NOT NULL,
--   related_to INTEGER NOT NULL,

--   CONSTRAINT tag_id_fk FOREIGN KEY (tag_id) REFERENCES tag_def (tag_id) ON DELETE CASCADE,
--   CONSTRAINT related_to_fk FOREIGN KEY (related_to) REFERENCES tag_def (tag_id) ON DELETE CASCADE,
--   CONSTRAINT relation_unique UNIQUE (tag_id, related_to)
-- );

-- CREATE TABLE IF NOT EXISTS image_tag (
--   image_id INTEGER NOT NULL,
--   tag_id INTEGER NOT NULL,
--   tagged_by INTEGER NOT NULL,

--   CONSTRAINT image_id_fk FOREIGN KEY (image_id) 
--     REFERENCES archive (image_id) ON DELETE CASCADE,
--   CONSTRAINT tag_id_fk FOREIGN KEY (tag_id) 
--     REFERENCES tag_def (tag_id) ON DELETE CASCADE,
--   CONSTRAINT tagged_by_fk FOREIGN KEY (tagged_by)
--     REFERENCES contributor (contributor_id) ON DELETE NO ACTION,
--   CONSTRAINT image_tag_unique UNIQUE (image_id, tag_id)
-- );
