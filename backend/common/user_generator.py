"""
Random user generator for testing and demo purposes.
"""
import random
import string
import csv
from pathlib import Path
from typing import List, Dict
import secrets


class UserGenerator:
    """Generate random users for testing"""
    
    FIRST_NAMES = [
        "James", "Mary", "John", "Patricia", "Robert", "Jennifer", "Michael", "Linda",
        "William", "Barbara", "David", "Elizabeth", "Richard", "Susan", "Joseph", "Jessica",
        "Thomas", "Sarah", "Charles", "Karen", "Christopher", "Nancy", "Daniel", "Lisa",
        "Matthew", "Betty", "Anthony", "Margaret", "Mark", "Sandra", "Donald", "Ashley",
        "Steven", "Kimberly", "Paul", "Emily", "Andrew", "Donna", "Joshua", "Michelle",
        "Wei", "Ming", "Hui", "Ling", "Jie", "Yan", "Lei", "Fang", "Xin", "Yue"
    ]
    
    LAST_NAMES = [
        "Smith", "Johnson", "Williams", "Brown", "Jones", "Garcia", "Miller", "Davis",
        "Rodriguez", "Martinez", "Hernandez", "Lopez", "Gonzalez", "Wilson", "Anderson",
        "Thomas", "Taylor", "Moore", "Jackson", "Martin", "Lee", "Thompson", "White",
        "Wang", "Zhang", "Li", "Liu", "Chen", "Yang", "Huang", "Zhao", "Wu", "Zhou"
    ]
    
    @staticmethod
    def generate_username(first_name: str, last_name: str, suffix: str = "") -> str:
        """Generate a username from name"""
        base = f"{first_name.lower()}.{last_name.lower()}"
        if suffix:
            return f"{base}{suffix}"
        return base
    
    @staticmethod
    def generate_password(length: int = 12) -> str:
        """Generate a random password"""
        return secrets.token_urlsafe(length)
    
    @staticmethod
    def generate_student_id() -> str:
        """Generate a random student ID"""
        return f"S{random.randint(100000, 999999)}"
    
    @classmethod
    def generate_users(
        cls,
        count: int,
        user_type: str = "student",
        with_passwords: bool = True
    ) -> List[Dict[str, str]]:
        """
        Generate random users.
        
        Args:
            count: Number of users to generate
            user_type: Type of user (student/teacher)
            with_passwords: Include random passwords
        
        Returns:
            List of user dictionaries
        """
        users = []
        used_usernames = set()
        
        for i in range(count):
            # Generate name
            first_name = random.choice(cls.FIRST_NAMES)
            last_name = random.choice(cls.LAST_NAMES)
            
            # Generate unique username
            username = cls.generate_username(first_name, last_name)
            suffix = 1
            while username in used_usernames:
                username = cls.generate_username(first_name, last_name, str(suffix))
                suffix += 1
            
            used_usernames.add(username)
            
            # Create user dict
            user = {
                "username": username,
                "name": f"{first_name} {last_name}",
                "email": f"{username}@example.com",
            }
            
            if with_passwords:
                user["password"] = cls.generate_password()
            
            if user_type == "student":
                user["student_id"] = cls.generate_student_id()
            
            users.append(user)
        
        return users
    
    @classmethod
    def save_to_csv(cls, users: List[Dict[str, str]], output_path: Path):
        """Save users to CSV file"""
        if not users:
            return
        
        fieldnames = list(users[0].keys())
        
        with open(output_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(users)
        
        print(f"Generated {len(users)} users and saved to {output_path}")


def main():
    """CLI for random user generation"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Generate random users")
    parser.add_argument("count", type=int, help="Number of users to generate")
    parser.add_argument("--type", choices=["student", "teacher"], default="student",
                       help="User type")
    parser.add_argument("--output", required=True, help="Output CSV file")
    parser.add_argument("--no-passwords", action="store_true",
                       help="Don't generate passwords")
    
    args = parser.parse_args()
    
    # Generate users
    users = UserGenerator.generate_users(
        count=args.count,
        user_type=args.type,
        with_passwords=not args.no_passwords
    )
    
    # Save to CSV
    UserGenerator.save_to_csv(users, Path(args.output))
    
    # Print summary
    print(f"\n{'='*60}")
    print(f"Generated {len(users)} {args.type}s")
    print(f"{'='*60}\n")
    
    print("Sample users:")
    for user in users[:5]:
        print(f"  {user['username']} - {user['name']}")
        if 'password' in user:
            print(f"    Password: {user['password']}")
    
    if len(users) > 5:
        print(f"  ... and {len(users) - 5} more")


if __name__ == "__main__":
    main()
