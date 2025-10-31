"""
Utility for importing users from CSV file.
Supports batch import of students and teachers.
"""
import csv
import asyncio
import httpx
from typing import List, Dict, Optional
from pathlib import Path
import sys


class UserImporter:
    """Import users from CSV file"""
    
    def __init__(self, auth_url: str, data_url: str, internal_token: str):
        self.auth_url = auth_url
        self.data_url = data_url
        self.internal_token = internal_token
        self.client = None
    
    async def __aenter__(self):
        self.client = httpx.AsyncClient(timeout=30.0)
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.client:
            await self.client.aclose()
    
    async def import_from_csv(
        self,
        csv_path: Path,
        admin_token: str,
        user_type: str = "student",
        generate_passwords: bool = False
    ) -> Dict[str, any]:
        """
        Import users from CSV file.
        
        CSV Format:
        username,password,name,email
        
        Args:
            csv_path: Path to CSV file
            admin_token: Admin access token
            user_type: Type of user (student/teacher)
            generate_passwords: If True, generate random passwords
        
        Returns:
            Dictionary with import results
        """
        results = {
            "success": [],
            "failed": [],
            "total": 0
        }
        
        with open(csv_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            
            for row in reader:
                results["total"] += 1
                username = row.get("username")
                password = row.get("password")
                name = row.get("name", username)
                
                if not username:
                    results["failed"].append({
                        "row": results["total"],
                        "error": "Missing username"
                    })
                    continue
                
                if not password and not generate_passwords:
                    results["failed"].append({
                        "row": results["total"],
                        "username": username,
                        "error": "Missing password"
                    })
                    continue
                
                # Generate password if needed
                if generate_passwords:
                    import secrets
                    password = secrets.token_urlsafe(12)
                
                # Import user
                try:
                    success = await self._import_single_user(
                        username=username,
                        password=password,
                        name=name,
                        user_type=user_type,
                        admin_token=admin_token
                    )
                    
                    if success:
                        results["success"].append({
                            "username": username,
                            "name": name,
                            "password": password if generate_passwords else "***"
                        })
                    else:
                        results["failed"].append({
                            "username": username,
                            "error": "Import failed"
                        })
                except Exception as e:
                    results["failed"].append({
                        "username": username,
                        "error": str(e)
                    })
        
        return results
    
    async def _import_single_user(
        self,
        username: str,
        password: str,
        name: str,
        user_type: str,
        admin_token: str
    ) -> bool:
        """Import a single user"""
        
        # Step 1: Generate registration code
        response = await self.client.post(
            f"{self.auth_url}/generate/registration-code",
            json={"user_type": user_type, "expires_days": 30},
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        
        if response.status_code not in [200, 201]:
            print(f"Failed to generate registration code for {username}")
            return False
        
        reg_code = response.json()["code"]
        
        # Step 2: Register user in auth system
        response = await self.client.post(
            f"{self.auth_url}/register/v1",
            json={
                "username": username,
                "password": password,
                "user_type": user_type,
                "registration_code": reg_code
            }
        )
        
        if response.status_code != 200:
            print(f"Failed to register {username}: {response.text}")
            return False
        
        # Step 3: Add to data node
        endpoint = f"/add/{'student' if user_type == 'student' else 'teacher'}"
        name_field = f"{'student' if user_type == 'student' else 'teacher'}_name"
        
        response = await self.client.post(
            f"{self.data_url}{endpoint}",
            json={name_field: name},
            headers={"Internal-Token": self.internal_token}
        )
        
        if response.status_code not in [200, 201, 400]:  # 400 if already exists
            print(f"Failed to add {username} to data node")
            return False
        
        return True


async def main():
    """CLI for CSV import"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Import users from CSV file")
    parser.add_argument("csv_file", help="Path to CSV file")
    parser.add_argument("--type", choices=["student", "teacher"], default="student",
                       help="User type")
    parser.add_argument("--admin-user", default="admin", help="Admin username")
    parser.add_argument("--admin-pass", default="admin123", help="Admin password")
    parser.add_argument("--generate-passwords", action="store_true",
                       help="Generate random passwords")
    parser.add_argument("--auth-url", default="http://localhost:8002",
                       help="Auth service URL")
    parser.add_argument("--data-url", default="http://localhost:8001",
                       help="Data service URL")
    parser.add_argument("--internal-token", default="change-this-internal-token",
                       help="Internal service token")
    parser.add_argument("--output", help="Output file for results")
    
    args = parser.parse_args()
    
    # Get admin token
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{args.auth_url}/login/admin",
            json={"username": args.admin_user, "password": args.admin_pass}
        )
        
        if response.status_code != 200:
            print("Failed to login as admin")
            sys.exit(1)
        
        admin_token = response.json()["access_token"]
    
    # Import users
    async with UserImporter(args.auth_url, args.data_url, args.internal_token) as importer:
        results = await importer.import_from_csv(
            Path(args.csv_file),
            admin_token,
            args.type,
            args.generate_passwords
        )
    
    # Print results
    print(f"\n{'='*60}")
    print(f"Import completed: {len(results['success'])}/{results['total']} successful")
    print(f"{'='*60}\n")
    
    if results["success"]:
        print("✓ Successfully imported:")
        for user in results["success"]:
            print(f"  - {user['username']} ({user['name']})")
            if args.generate_passwords and user['password'] != '***':
                print(f"    Password: {user['password']}")
    
    if results["failed"]:
        print("\n✗ Failed imports:")
        for failure in results["failed"]:
            print(f"  - {failure.get('username', 'Unknown')}: {failure['error']}")
    
    # Write results to file if requested
    if args.output:
        with open(args.output, 'w', encoding='utf-8') as f:
            f.write("username,password,name,status\n")
            for user in results["success"]:
                f.write(f"{user['username']},{user.get('password', '***')},{user['name']},success\n")
            for failure in results["failed"]:
                f.write(f"{failure.get('username', 'N/A')},,,failed: {failure['error']}\n")
        
        print(f"\nResults written to: {args.output}")


if __name__ == "__main__":
    asyncio.run(main())
