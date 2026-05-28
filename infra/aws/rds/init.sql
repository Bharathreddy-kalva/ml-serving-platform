-- Run once against the RDS instance after provisioning.
-- Creates the application database and role; migrations are handled by Alembic.

CREATE ROLE mlserving WITH LOGIN PASSWORD 'CHANGE_ME_IN_SECRETS_MANAGER';
CREATE DATABASE mlserving OWNER mlserving;
GRANT ALL PRIVILEGES ON DATABASE mlserving TO mlserving;
