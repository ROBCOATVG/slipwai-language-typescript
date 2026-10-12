export const up = (pgm) => {
  pgm.sql(`CREATE TABLE states (
    id TEXT PRIMARY KEY,
    version INTEGER NOT NULL CHECK (version >= 0),
    state JSONB NOT NULL CHECK (jsonb_typeof(state) = 'object')
  );`);
};
export const down = (pgm) => {
  pgm.sql('DROP TABLE states;');
};
