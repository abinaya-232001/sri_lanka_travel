-- Store image links for attraction cards (Google search or direct URLs)
ALTER TABLE attractions ADD COLUMN IF NOT EXISTS image TEXT;
