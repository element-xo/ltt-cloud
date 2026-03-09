"""
Setup script for MSSQL test database with RLS (Row-Level Security).

Run in CI to create the ltt_lca_test database, tables, and seed data
before pytest executes.  Requires MSSQL_CONNECTION_STRING env var
pointing to the SA account on the CI SQL Server container.
"""

import os
import uuid

import pyodbc


def main():
    conn_str = os.getenv("MSSQL_CONNECTION_STRING")
    if not conn_str:
        raise RuntimeError("MSSQL_CONNECTION_STRING env var is required")

    # ------------------------------------------------------------------
    # Connect to master to create the test database
    # ------------------------------------------------------------------
    master_str = conn_str.replace("/master", "/master")
    conn = pyodbc.connect(master_str, autocommit=True)
    cursor = conn.cursor()

    cursor.execute("""
        IF NOT EXISTS (SELECT name FROM sys.databases WHERE name = 'ltt_lca_test')
            CREATE DATABASE ltt_lca_test
    """)
    conn.close()

    # ------------------------------------------------------------------
    # Connect to ltt_lca_test and create schema + RLS
    # ------------------------------------------------------------------
    test_str = conn_str.replace("/master", "/ltt_lca_test")
    conn = pyodbc.connect(test_str, autocommit=True)
    cursor = conn.cursor()

    # Tables
    cursor.execute("""
        IF OBJECT_ID('ltt_scenarios', 'U') IS NULL
        CREATE TABLE ltt_scenarios (
            id         NVARCHAR(36) PRIMARY KEY,
            owner_id   NVARCHAR(36) NOT NULL,
            name       NVARCHAR(255),
            co2_mass   FLOAT
        )
    """)

    cursor.execute("""
        IF OBJECT_ID('ltt_users', 'U') IS NULL
        CREATE TABLE ltt_users (
            id    NVARCHAR(36) PRIMARY KEY,
            email NVARCHAR(255) UNIQUE NOT NULL
        )
    """)

    # ------------------------------------------------------------------
    # RLS: filter predicate so users only see their own scenarios
    # ------------------------------------------------------------------
    cursor.execute("""
        IF NOT EXISTS (SELECT * FROM sys.schemas WHERE name = 'rls')
            EXEC('CREATE SCHEMA rls')
    """)

    cursor.execute("""
        IF OBJECT_ID('rls.fn_scenario_access', 'IF') IS NOT NULL
            DROP FUNCTION rls.fn_scenario_access
    """)
    cursor.execute("""
        CREATE FUNCTION rls.fn_scenario_access(@owner_id NVARCHAR(36))
        RETURNS TABLE
        WITH SCHEMABINDING
        AS
        RETURN SELECT 1 AS access
               WHERE @owner_id = CONVERT(NVARCHAR(36), SESSION_CONTEXT(N'user_id'))
    """)

    # Security policy (drop first if exists)
    cursor.execute("""
        IF EXISTS (SELECT * FROM sys.security_policies WHERE name = 'ScenarioFilter')
            DROP SECURITY POLICY ScenarioFilter
    """)
    cursor.execute("""
        CREATE SECURITY POLICY ScenarioFilter
        ADD FILTER PREDICATE rls.fn_scenario_access(owner_id)
        ON dbo.ltt_scenarios
        WITH (STATE = ON)
    """)

    # ------------------------------------------------------------------
    # Seed data
    # ------------------------------------------------------------------
    user1_id = str(uuid.uuid4())
    user2_id = str(uuid.uuid4())

    cursor.execute(
        "INSERT INTO ltt_users (id, email) VALUES (?, ?)",
        (user1_id, "user1@ltt.rwth-aachen.de"),
    )
    cursor.execute(
        "INSERT INTO ltt_users (id, email) VALUES (?, ?)",
        (user2_id, "user2@ltt.rwth-aachen.de"),
    )

    cursor.execute(
        "INSERT INTO ltt_scenarios (id, owner_id, name, co2_mass) VALUES (?, ?, ?, ?)",
        (str(uuid.uuid4()), user1_id, "P2X Baseline", 10.0),
    )
    cursor.execute(
        "INSERT INTO ltt_scenarios (id, owner_id, name, co2_mass) VALUES (?, ?, ?, ?)",
        (str(uuid.uuid4()), user2_id, "Solar Hydrogen", 20.0),
    )

    conn.close()
    print("MSSQL test database setup complete.")


if __name__ == "__main__":
    main()
