DROP FUNCTION IF EXISTS reset_availbility CASCADE;
DROP TRIGGER IF EXISTS reset_availbility ON car_availability CASCADE;
DROP TABLE IF EXISTS car_availability;
DROP TABLE IF EXISTS bookings;
DROP TABLE IF EXISTS cars;

CREATE TABLE cars (
  number_plate TEXT PRIMARY KEY,
  make TEXT NOT NULL,
  model TEXT NOT NULL,
  colour TEXT NOT NULL,
  capacity TEXT NOT NULL
);

CREATE TABLE bookings (
  booking_id SERIAL PRIMARY KEY,
  user_name TEXT NOT NULL,
  car_id TEXT NOT NULL,
  created TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  pickup TIMESTAMP NOT NULL,
  drop_off TIMESTAMP NOT NULL,
  booking_title TEXT NOT NULL,
  description TEXT NOT NULL,
  approved BOOLEAN NOT NULL DEFAULT false,
  FOREIGN KEY (car_id) REFERENCES cars (number_plate)
);

CREATE TABLE car_availability (
  car_id TEXT NOT NULL,
  available BOOLEAN NOT NULL,
  expires TIMESTAMP DEFAULT NULL,
  PRIMARY KEY(car_id),
  FOREIGN KEY (car_id) REFERENCES cars (number_plate)
);

CREATE FUNCTION reset_availbility() RETURNS trigger
    LANGUAGE plpgsql
    AS $$
DECLARE
  row_count int;
BEGIN
  UPDATE car_availability SET available = 'true', expires = NULL WHERE expires < NOW() - INTERVAL '1 days';
    IF found THEN
      GET DIAGNOSTICS row_count = ROW_COUNT;
      RAISE NOTICE 'Updated % row(s) FROM car_availability', row_count;
  END IF;
  RETURN NULL;
END;
$$;

CREATE TRIGGER reset_availbility
    AFTER INSERT ON car_availability
    EXECUTE PROCEDURE reset_availbility();