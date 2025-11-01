"""
DB Edit CLI Tool
Provides direct database editing capabilities with full permissions.
WARNING: This tool bypasses all application logic and constraints.
"""
import click
import asyncio
from sqlalchemy import inspect, MetaData, Table, select, update, delete, insert
from sqlalchemy.orm import Session
from tabulate import tabulate
from typing import List, Dict, Any
import json
from pathlib import Path

from backend.common.database import create_db_engine, create_session_factory, get_db_session
from backend.common.models import Base, Course, Student, Teacher, Admin, RefreshToken, RegistrationCode, ResetCode


# Available databases
DATABASES = {
    'data': {
        'path': './course_data.db',
        'models': [Course, Student, Teacher]
    },
    'auth': {
        'path': './auth_data.db',
        'models': [Admin, RefreshToken, RegistrationCode, ResetCode]
    },
    'queue': {
        'path': './queue_data.db',
        'models': []  # Queue database has custom models
    }
}


@click.group()
def db_edit():
    """Database editor - Direct database modification tool with full permissions"""
    pass


@db_edit.command()
@click.option('--database', '-d', type=click.Choice(['data', 'auth', 'queue']), required=True, help='Database to edit')
def list_tables(database):
    """List all tables in the database"""
    db_path = DATABASES[database]['path']
    
    if not Path(db_path).exists():
        click.echo(click.style(f'✗ Database not found: {db_path}', fg='red'))
        return
    
    engine = create_db_engine(f'sqlite:///{db_path}')
    inspector = inspect(engine)
    tables = inspector.get_table_names()
    
    if not tables:
        click.echo(click.style('No tables found in database', fg='yellow'))
        return
    
    click.echo(click.style(f'\nTables in {database} database:', bold=True))
    for table in tables:
        columns = inspector.get_columns(table)
        click.echo(f'\n  📋 {click.style(table, fg="cyan", bold=True)} ({len(columns)} columns)')
        
        # Show column names
        col_names = [col['name'] for col in columns]
        click.echo(f'     Columns: {", ".join(col_names)}')


@db_edit.command()
@click.option('--database', '-d', type=click.Choice(['data', 'auth', 'queue']), required=True, help='Database to query')
@click.option('--table', '-t', required=True, help='Table name')
@click.option('--limit', '-l', default=50, help='Limit number of rows')
@click.option('--format', '-f', type=click.Choice(['table', 'json']), default='table', help='Output format')
def query(database, table, limit, format):
    """Query records from a table"""
    db_path = DATABASES[database]['path']
    
    if not Path(db_path).exists():
        click.echo(click.style(f'✗ Database not found: {db_path}', fg='red'))
        return
    
    engine = create_db_engine(f'sqlite:///{db_path}')
    SessionLocal = create_session_factory(engine)
    
    with get_db_session(SessionLocal) as session:
        # Use SQLAlchemy core for generic table access
        metadata = MetaData()
        metadata.reflect(bind=engine)
        
        if table not in metadata.tables:
            click.echo(click.style(f'✗ Table not found: {table}', fg='red'))
            return
        
        table_obj = metadata.tables[table]
        stmt = select(table_obj).limit(limit)
        result = session.execute(stmt)
        rows = result.fetchall()
        
        if not rows:
            click.echo(click.style('No records found', fg='yellow'))
            return
        
        # Convert to dict
        columns = [col.name for col in table_obj.columns]
        data = []
        for row in rows:
            data.append(dict(zip(columns, row)))
        
        if format == 'json':
            click.echo(json.dumps(data, indent=2, default=str))
        else:
            click.echo(f'\n{click.style(f"Records from {table}:", bold=True)} (showing {len(data)} of {len(data)})\n')
            click.echo(tabulate(data, headers='keys', tablefmt='grid'))


@db_edit.command()
@click.option('--database', '-d', type=click.Choice(['data', 'auth', 'queue']), required=True, help='Database to edit')
@click.option('--table', '-t', required=True, help='Table name')
@click.option('--values', '-v', required=True, help='JSON string of column=value pairs')
def insert_record(database, table, values):
    """Insert a new record into a table"""
    db_path = DATABASES[database]['path']
    
    if not Path(db_path).exists():
        click.echo(click.style(f'✗ Database not found: {db_path}', fg='red'))
        return
    
    try:
        values_dict = json.loads(values)
    except json.JSONDecodeError:
        click.echo(click.style('✗ Invalid JSON format for values', fg='red'))
        return
    
    engine = create_db_engine(f'sqlite:///{db_path}')
    SessionLocal = create_session_factory(engine)
    
    with get_db_session(SessionLocal) as session:
        metadata = MetaData()
        metadata.reflect(bind=engine)
        
        if table not in metadata.tables:
            click.echo(click.style(f'✗ Table not found: {table}', fg='red'))
            return
        
        table_obj = metadata.tables[table]
        
        try:
            stmt = insert(table_obj).values(**values_dict)
            result = session.execute(stmt)
            session.commit()
            
            click.echo(click.style(f'✓ Record inserted successfully! ID: {result.lastrowid}', fg='green'))
        except Exception as e:
            session.rollback()
            click.echo(click.style(f'✗ Failed to insert record: {str(e)}', fg='red'))


@db_edit.command()
@click.option('--database', '-d', type=click.Choice(['data', 'auth', 'queue']), required=True, help='Database to edit')
@click.option('--table', '-t', required=True, help='Table name')
@click.option('--where', '-w', required=True, help='WHERE condition (JSON format)')
@click.option('--values', '-v', required=True, help='JSON string of column=value pairs to update')
def update_record(database, table, where, values):
    """Update records in a table"""
    db_path = DATABASES[database]['path']
    
    if not Path(db_path).exists():
        click.echo(click.style(f'✗ Database not found: {db_path}', fg='red'))
        return
    
    try:
        where_dict = json.loads(where)
        values_dict = json.loads(values)
    except json.JSONDecodeError:
        click.echo(click.style('✗ Invalid JSON format', fg='red'))
        return
    
    # Confirm action
    if not click.confirm(f'Are you sure you want to update records in {table} where {where}?'):
        click.echo('Cancelled')
        return
    
    engine = create_db_engine(f'sqlite:///{db_path}')
    SessionLocal = create_session_factory(engine)
    
    with get_db_session(SessionLocal) as session:
        metadata = MetaData()
        metadata.reflect(bind=engine)
        
        if table not in metadata.tables:
            click.echo(click.style(f'✗ Table not found: {table}', fg='red'))
            return
        
        table_obj = metadata.tables[table]
        
        try:
            # Build WHERE clause
            stmt = update(table_obj).values(**values_dict)
            for key, value in where_dict.items():
                stmt = stmt.where(table_obj.c[key] == value)
            
            result = session.execute(stmt)
            session.commit()
            
            click.echo(click.style(f'✓ Updated {result.rowcount} record(s) successfully!', fg='green'))
        except Exception as e:
            session.rollback()
            click.echo(click.style(f'✗ Failed to update records: {str(e)}', fg='red'))


@db_edit.command()
@click.option('--database', '-d', type=click.Choice(['data', 'auth', 'queue']), required=True, help='Database to edit')
@click.option('--table', '-t', required=True, help='Table name')
@click.option('--where', '-w', required=True, help='WHERE condition (JSON format)')
def delete_record(database, table, where):
    """Delete records from a table"""
    db_path = DATABASES[database]['path']
    
    if not Path(db_path).exists():
        click.echo(click.style(f'✗ Database not found: {db_path}', fg='red'))
        return
    
    try:
        where_dict = json.loads(where)
    except json.JSONDecodeError:
        click.echo(click.style('✗ Invalid JSON format for WHERE condition', fg='red'))
        return
    
    # Confirm action
    if not click.confirm(click.style(f'⚠ WARNING: Are you sure you want to DELETE records from {table} where {where}?', fg='red', bold=True)):
        click.echo('Cancelled')
        return
    
    engine = create_db_engine(f'sqlite:///{db_path}')
    SessionLocal = create_session_factory(engine)
    
    with get_db_session(SessionLocal) as session:
        metadata = MetaData()
        metadata.reflect(bind=engine)
        
        if table not in metadata.tables:
            click.echo(click.style(f'✗ Table not found: {table}', fg='red'))
            return
        
        table_obj = metadata.tables[table]
        
        try:
            # Build WHERE clause
            stmt = delete(table_obj)
            for key, value in where_dict.items():
                stmt = stmt.where(table_obj.c[key] == value)
            
            result = session.execute(stmt)
            session.commit()
            
            click.echo(click.style(f'✓ Deleted {result.rowcount} record(s) successfully!', fg='green'))
        except Exception as e:
            session.rollback()
            click.echo(click.style(f'✗ Failed to delete records: {str(e)}', fg='red'))


@db_edit.command()
@click.option('--database', '-d', type=click.Choice(['data', 'auth', 'queue']), required=True, help='Database to query')
@click.option('--table', '-t', required=True, help='Table name')
@click.option('--column', '-c', required=True, help='Column name')
def column_info(database, table, column):
    """Get detailed information about a column"""
    db_path = DATABASES[database]['path']
    
    if not Path(db_path).exists():
        click.echo(click.style(f'✗ Database not found: {db_path}', fg='red'))
        return
    
    engine = create_db_engine(f'sqlite:///{db_path}')
    inspector = inspect(engine)
    
    if table not in inspector.get_table_names():
        click.echo(click.style(f'✗ Table not found: {table}', fg='red'))
        return
    
    columns = inspector.get_columns(table)
    col_info = next((col for col in columns if col['name'] == column), None)
    
    if not col_info:
        click.echo(click.style(f'✗ Column not found: {column}', fg='red'))
        return
    
    click.echo(f'\n{click.style(f"Column: {column}", bold=True)}')
    click.echo(f'  Type: {col_info["type"]}')
    click.echo(f'  Nullable: {col_info["nullable"]}')
    click.echo(f'  Default: {col_info.get("default", "None")}')
    click.echo(f'  Primary Key: {col_info.get("primary_key", False)}')


@db_edit.command()
@click.option('--database', '-d', type=click.Choice(['data', 'auth', 'queue']), required=True, help='Database to query')
@click.option('--sql', '-s', required=True, help='Raw SQL query to execute')
@click.option('--format', '-f', type=click.Choice(['table', 'json']), default='table', help='Output format')
def raw_query(database, sql, format):
    """Execute a raw SQL query (SELECT only for safety)"""
    db_path = DATABASES[database]['path']
    
    if not Path(db_path).exists():
        click.echo(click.style(f'✗ Database not found: {db_path}', fg='red'))
        return
    
    # Safety check - only allow SELECT
    if not sql.strip().upper().startswith('SELECT'):
        click.echo(click.style('✗ Only SELECT queries are allowed for safety', fg='red'))
        click.echo('Use specific commands (insert-record, update-record, delete-record) for modifications')
        return
    
    engine = create_db_engine(f'sqlite:///{db_path}')
    SessionLocal = create_session_factory(engine)
    
    with get_db_session(SessionLocal) as session:
        try:
            result = session.execute(sql)
            rows = result.fetchall()
            
            if not rows:
                click.echo(click.style('No results', fg='yellow'))
                return
            
            # Get column names
            columns = result.keys()
            data = [dict(zip(columns, row)) for row in rows]
            
            if format == 'json':
                click.echo(json.dumps(data, indent=2, default=str))
            else:
                click.echo(f'\n{click.style("Query Results:", bold=True)} ({len(data)} rows)\n')
                click.echo(tabulate(data, headers='keys', tablefmt='grid'))
        except Exception as e:
            click.echo(click.style(f'✗ Query failed: {str(e)}', fg='red'))


if __name__ == '__main__':
    db_edit()
