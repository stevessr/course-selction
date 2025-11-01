"""
CLI Tool for User Management
Provides command-line interface for managing users, courses, and system operations.
"""
import click
import asyncio
import httpx
import os
from typing import Optional
from pathlib import Path
from datetime import datetime
import json
from getpass import getpass
from tabulate import tabulate


class CLIClient:
    """HTTP/Socket client for CLI operations"""
    
    def __init__(self, auth_url: str, data_url: str, internal_token: str):
        self.auth_url = auth_url
        self.data_url = data_url
        self.internal_token = internal_token
        self.admin_token: Optional[str] = None
    
    async def login_admin(self, username: str, password: str) -> bool:
        """Login as admin"""
        async with httpx.AsyncClient(timeout=30.0) as client:
            try:
                response = await client.post(
                    f"{self.auth_url}/admin/login",
                    json={"username": username, "password": password}
                )
                if response.status_code == 200:
                    data = response.json()
                    self.admin_token = data["access_token"]
                    return True
                return False
            except Exception as e:
                click.echo(f"Login failed: {e}", err=True)
                return False
    
    def get_headers(self):
        """Get request headers"""
        headers = {"Internal-Token": self.internal_token}
        if self.admin_token:
            headers["Authorization"] = f"Bearer {self.admin_token}"
        return headers


@click.group()
def cli():
    """Course Selection System - User Management CLI"""
    pass


@cli.group()
def user():
    """User management commands"""
    pass


@user.command()
@click.option('--username', prompt=True, help='Admin username')
@click.option('--password', prompt=True, hide_input=True, help='Admin password')
@click.option('--auth-url', default='http://localhost:8002', help='Auth node URL')
@click.option('--internal-token', envvar='INTERNAL_TOKEN', default='change-this-internal-token')
def login(username: str, password: str, auth_url: str, internal_token: str):
    """Login as admin and save session"""
    async def _login():
        client = CLIClient(auth_url, '', internal_token)
        if await client.login_admin(username, password):
            # Save token to config file
            config_dir = Path.home() / '.course_selection'
            config_dir.mkdir(exist_ok=True)
            config_file = config_dir / 'config.json'
            config_file.write_text(json.dumps({
                'admin_token': client.admin_token,
                'auth_url': auth_url,
                'internal_token': internal_token,
                'login_time': datetime.now().isoformat()
            }))
            click.echo(click.style('✓ Login successful', fg='green'))
        else:
            click.echo(click.style('✗ Login failed', fg='red'))
    
    asyncio.run(_login())


@user.command()
@click.option('--username', required=True, help='Student username')
@click.option('--password', prompt=True, hide_input=True, confirmation_prompt=True)
@click.option('--name', required=True, help='Student full name')
@click.option('--email', required=True, help='Student email')
@click.option('--group', default='default', help='Student group')
def add_student(username: str, password: str, name: str, email: str, group: str):
    """Add a new student"""
    async def _add():
        # Load config
        config = load_config()
        client = CLIClient(config['auth_url'], 
                          os.getenv('DATA_NODE_URL', 'http://localhost:8001'),
                          config['internal_token'])
        client.admin_token = config['admin_token']
        
        async with httpx.AsyncClient(timeout=30.0) as http_client:
            # Generate registration code
            try:
                response = await http_client.post(
                    f"{config['auth_url']}/admin/registration-codes",
                    json={"user_type": "student", "max_uses": 1},
                    headers=client.get_headers()
                )
                if response.status_code != 200:
                    click.echo(click.style(f'✗ Failed to generate registration code', fg='red'))
                    return
                
                reg_code = response.json()['code']
                
                # Register student
                response = await http_client.post(
                    f"{config['auth_url']}/register",
                    json={
                        "username": username,
                        "password": password,
                        "name": name,
                        "email": email,
                        "registration_code": reg_code
                    }
                )
                
                if response.status_code == 200:
                    data = response.json()
                    click.echo(click.style('✓ Student created successfully', fg='green'))
                    click.echo(f"  ID: {data['id']}")
                    click.echo(f"  Username: {data['username']}")
                    click.echo(f"  2FA Secret: {data['totp_secret']}")
                    click.echo(f"  2FA QR URI: {data['totp_uri']}")
                else:
                    click.echo(click.style(f'✗ Failed: {response.text}', fg='red'))
            
            except Exception as e:
                click.echo(click.style(f'✗ Error: {e}', fg='red'))
    
    asyncio.run(_add())


@user.command()
@click.option('--username', required=True, help='Teacher username')
@click.option('--password', prompt=True, hide_input=True, confirmation_prompt=True)
@click.option('--name', required=True, help='Teacher full name')
@click.option('--email', required=True, help='Teacher email')
def add_teacher(username: str, password: str, name: str, email: str):
    """Add a new teacher"""
    async def _add():
        config = load_config()
        
        async with httpx.AsyncClient(timeout=30.0) as http_client:
            try:
                # Generate registration code
                response = await http_client.post(
                    f"{config['auth_url']}/admin/registration-codes",
                    json={"user_type": "teacher", "max_uses": 1},
                    headers={"Authorization": f"Bearer {config['admin_token']}",
                            "Internal-Token": config['internal_token']}
                )
                
                if response.status_code != 200:
                    click.echo(click.style(f'✗ Failed to generate registration code', fg='red'))
                    return
                
                reg_code = response.json()['code']
                
                # Register teacher
                response = await http_client.post(
                    f"{config['auth_url']}/register/teacher",
                    json={
                        "username": username,
                        "password": password,
                        "name": name,
                        "email": email,
                        "registration_code": reg_code
                    }
                )
                
                if response.status_code == 200:
                    data = response.json()
                    click.echo(click.style('✓ Teacher created successfully', fg='green'))
                    click.echo(f"  ID: {data['id']}")
                    click.echo(f"  Username: {data['username']}")
                else:
                    click.echo(click.style(f'✗ Failed: {response.text}', fg='red'))
            
            except Exception as e:
                click.echo(click.style(f'✗ Error: {e}', fg='red'))
    
    asyncio.run(_add())


@user.command()
@click.option('--user-type', type=click.Choice(['student', 'teacher']), 
              default='student', help='User type to list')
def list(user_type: str):
    """List all users"""
    async def _list():
        config = load_config()
        
        async with httpx.AsyncClient(timeout=30.0) as http_client:
            try:
                if user_type == 'student':
                    response = await http_client.get(
                        f"{os.getenv('DATA_NODE_URL', 'http://localhost:8001')}/students",
                        headers={"Internal-Token": config['internal_token']}
                    )
                else:
                    response = await http_client.get(
                        f"{os.getenv('DATA_NODE_URL', 'http://localhost:8001')}/teachers",
                        headers={"Internal-Token": config['internal_token']}
                    )
                
                if response.status_code == 200:
                    users = response.json()
                    if not users:
                        click.echo(f"No {user_type}s found")
                        return
                    
                    # Format as table
                    headers = ['ID', 'Username', 'Name', 'Email']
                    rows = [[u['id'], u['username'], u['name'], u['email']] for u in users]
                    click.echo(tabulate(rows, headers=headers, tablefmt='grid'))
                else:
                    click.echo(click.style(f'✗ Failed to fetch users', fg='red'))
            
            except Exception as e:
                click.echo(click.style(f'✗ Error: {e}', fg='red'))
    
    asyncio.run(_list())


@user.command()
@click.argument('user_id', type=int)
@click.option('--user-type', type=click.Choice(['student', 'teacher']), 
              required=True, help='User type')
def delete(user_id: int, user_type: str):
    """Delete a user by ID"""
    if not click.confirm(f'Are you sure you want to delete {user_type} with ID {user_id}?'):
        return
    
    async def _delete():
        config = load_config()
        
        async with httpx.AsyncClient(timeout=30.0) as http_client:
            try:
                endpoint = 'students' if user_type == 'student' else 'teachers'
                response = await http_client.delete(
                    f"{os.getenv('DATA_NODE_URL', 'http://localhost:8001')}/{endpoint}/{user_id}",
                    headers={"Internal-Token": config['internal_token']}
                )
                
                if response.status_code == 200:
                    click.echo(click.style(f'✓ {user_type.capitalize()} deleted successfully', fg='green'))
                else:
                    click.echo(click.style(f'✗ Failed: {response.text}', fg='red'))
            
            except Exception as e:
                click.echo(click.style(f'✗ Error: {e}', fg='red'))
    
    asyncio.run(_delete())


@user.command()
@click.argument('username')
def reset_2fa(username: str):
    """Reset 2FA for a student"""
    async def _reset():
        config = load_config()
        
        async with httpx.AsyncClient(timeout=30.0) as http_client:
            try:
                response = await http_client.post(
                    f"{config['auth_url']}/admin/reset-codes",
                    json={"username": username},
                    headers={"Authorization": f"Bearer {config['admin_token']}",
                            "Internal-Token": config['internal_token']}
                )
                
                if response.status_code == 200:
                    data = response.json()
                    click.echo(click.style('✓ 2FA reset code generated', fg='green'))
                    click.echo(f"  Reset Code: {data['code']}")
                    click.echo(f"  Valid until: {data['expires_at']}")
                else:
                    click.echo(click.style(f'✗ Failed: {response.text}', fg='red'))
            
            except Exception as e:
                click.echo(click.style(f'✗ Error: {e}', fg='red'))
    
    asyncio.run(_reset())


@cli.group()
def code():
    """Registration and reset code management"""
    pass


@code.command()
@click.option('--user-type', type=click.Choice(['student', 'teacher']),
              required=True, help='User type')
@click.option('--max-uses', default=1, help='Maximum number of uses')
def generate(user_type: str, max_uses: int):
    """Generate registration code"""
    async def _generate():
        config = load_config()
        
        async with httpx.AsyncClient(timeout=30.0) as http_client:
            try:
                response = await http_client.post(
                    f"{config['auth_url']}/admin/registration-codes",
                    json={"user_type": user_type, "max_uses": max_uses},
                    headers={"Authorization": f"Bearer {config['admin_token']}",
                            "Internal-Token": config['internal_token']}
                )
                
                if response.status_code == 200:
                    data = response.json()
                    click.echo(click.style('✓ Registration code generated', fg='green'))
                    click.echo(f"  Code: {data['code']}")
                    click.echo(f"  Type: {data['user_type']}")
                    click.echo(f"  Max uses: {data['max_uses']}")
                    click.echo(f"  Valid until: {data['expires_at']}")
                else:
                    click.echo(click.style(f'✗ Failed: {response.text}', fg='red'))
            
            except Exception as e:
                click.echo(click.style(f'✗ Error: {e}', fg='red'))
    
    asyncio.run(_generate())


@cli.group()
def import_cmd():
    """Import data from files"""
    pass


@import_cmd.command()
@click.argument('csv_file', type=click.Path(exists=True))
@click.option('--user-type', type=click.Choice(['student', 'teacher']),
              required=True, help='User type to import')
@click.option('--generate-passwords', is_flag=True, help='Generate random passwords')
@click.option('--output', type=click.Path(), help='Output CSV file with results')
def csv(csv_file: str, user_type: str, generate_passwords: bool, output: Optional[str]):
    """Import users from CSV file"""
    click.echo(f"Importing {user_type}s from {csv_file}...")
    
    async def _import():
        from backend.common.csv_import import UserImporter
        
        config = load_config()
        
        async with UserImporter(
            config['auth_url'],
            os.getenv('DATA_NODE_URL', 'http://localhost:8001'),
            config['internal_token']
        ) as importer:
            results = await importer.import_from_csv(
                Path(csv_file),
                config['admin_token'],
                user_type,
                generate_passwords
            )
            
            click.echo(f"\n{click.style('Import Results:', bold=True)}")
            click.echo(f"  Total: {results['total']}")
            click.echo(f"  {click.style('Success:', fg='green')} {results['success']}")
            click.echo(f"  {click.style('Failed:', fg='red')} {results['failed']}")
            
            if output and results.get('details'):
                import csv as csv_module
                with open(output, 'w', newline='') as f:
                    writer = csv_module.DictWriter(f, fieldnames=['username', 'status', 'message'])
                    writer.writeheader()
                    writer.writerows(results['details'])
                click.echo(f"\nDetails written to {output}")
    
    asyncio.run(_import())


@cli.command()
def status():
    """Check system status"""
    async def _status():
        services = [
            ('Data Node', os.getenv('DATA_NODE_URL', 'http://localhost:8001')),
            ('Auth Node', os.getenv('AUTH_NODE_URL', 'http://localhost:8002')),
            ('Teacher Node', os.getenv('TEACHER_NODE_URL', 'http://localhost:8003')),
            ('Student Node', os.getenv('STUDENT_NODE_URL', 'http://localhost:8004')),
            ('Queue Node', os.getenv('QUEUE_NODE_URL', 'http://localhost:8005')),
        ]
        
        click.echo(click.style('System Status:', bold=True))
        
        async with httpx.AsyncClient(timeout=5.0) as client:
            for name, url in services:
                try:
                    response = await client.get(f"{url}/health")
                    if response.status_code == 200:
                        click.echo(f"  {click.style('●', fg='green')} {name}: {click.style('online', fg='green')}")
                    else:
                        click.echo(f"  {click.style('●', fg='yellow')} {name}: {click.style('degraded', fg='yellow')}")
                except:
                    click.echo(f"  {click.style('●', fg='red')} {name}: {click.style('offline', fg='red')}")
    
    asyncio.run(_status())


def load_config():
    """Load saved CLI configuration"""
    config_file = Path.home() / '.course_selection' / 'config.json'
    if not config_file.exists():
        click.echo(click.style('✗ Not logged in. Please run: course-cli user login', fg='red'))
        raise click.Abort()
    
    config = json.loads(config_file.read_text())
    
    # Check if token is still valid (simple time-based check)
    login_time = datetime.fromisoformat(config['login_time'])
    if (datetime.now() - login_time).total_seconds() > 86400:  # 24 hours
        click.echo(click.style('✗ Session expired. Please login again.', fg='yellow'))
        raise click.Abort()
    
    return config


if __name__ == '__main__':
    cli()
