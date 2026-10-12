CREATE DATABASE places;
CREATE DATABASE forecasts;
CREATE DATABASE dashboard;
\connect places
CREATE TABLE places (id text PRIMARY KEY, name text NOT NULL, latitude double precision NOT NULL, longitude double precision NOT NULL);
CREATE TABLE request_outbox (id uuid PRIMARY KEY, payload jsonb NOT NULL, published boolean NOT NULL DEFAULT false, created_at timestamptz NOT NULL DEFAULT now());
\connect forecasts
CREATE TABLE places (id text PRIMARY KEY, name text NOT NULL, latitude double precision NOT NULL, longitude double precision NOT NULL);
CREATE TABLE forecasts (place_id text PRIMARY KEY, updated_at timestamptz NOT NULL, payload jsonb NOT NULL, expires_at timestamptz NOT NULL, last_modified text);
CREATE TABLE inbox (event_id text PRIMARY KEY, consumed_at timestamptz NOT NULL DEFAULT now());
CREATE TABLE forecast_outbox (id text PRIMARY KEY, payload jsonb NOT NULL, published boolean NOT NULL DEFAULT false);
CREATE TABLE rejected_messages (topic text NOT NULL, partition_id integer NOT NULL, offset_id bigint NOT NULL, reason text NOT NULL, PRIMARY KEY(topic,partition_id,offset_id));
\connect dashboard
CREATE TABLE weather_cards (place_id text PRIMARY KEY, name text NOT NULL, latitude double precision NOT NULL, longitude double precision NOT NULL, updated_at timestamptz, forecast jsonb);
CREATE TABLE inbox (event_id text PRIMARY KEY, consumed_at timestamptz NOT NULL DEFAULT now());
CREATE TABLE rejected_messages (topic text NOT NULL, partition_id integer NOT NULL, offset_id bigint NOT NULL, reason text NOT NULL, PRIMARY KEY(topic,partition_id,offset_id));
