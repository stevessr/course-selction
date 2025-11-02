# User Guide

Complete guide for using the Course Selection System.

## Table of Contents

- [Getting Started](#getting-started)
- [Student Guide](#student-guide)
- [Teacher Guide](#teacher-guide)
- [Administrator Guide](#administrator-guide)
- [FAQ](#faq)

## Getting Started

### Accessing the System

Open your web browser and navigate to the Course Selection System URL (e.g., http://localhost:3000)

### First Time Setup

#### For Students

1. Obtain a registration code from your administrator
2. Click "Register" on the login page
3. Fill in your information:
   - Username
   - Password (minimum 6 characters)
   - Registration code
4. Scan the QR code with an authenticator app (Google Authenticator, Authy, Microsoft Authenticator)
5. Save your secret key in a safe place
6. Enter the 6-digit code from your authenticator
7. You're ready to use the system!

#### For Teachers

1. Obtain a registration code from your administrator
2. Register with your credentials
3. Teachers don't need 2FA - you can login directly

#### For Administrators

Contact the system administrator for your credentials.

## Student Guide

### Logging In

1. Enter your username and password
2. Click "Login"
3. Open your authenticator app
4. Enter the 6-digit code
5. Click "Verify"

### Browsing Courses

1. Navigate to "Available Courses"
2. Use filters to find courses:
   - By type (Required/Elective)
   - By search keyword
3. View course details:
   - Course name and credits
   - Teacher name
   - Location
   - Available seats

### Selecting Courses

1. Find a course you want to enroll in
2. Click "Select" button
3. The request will be added to the queue
4. Wait for confirmation (usually 2-5 seconds)
5. Check "My Courses" to see enrolled courses

**Note:** There's a rate limit of 10 course selections per minute to ensure fair access during peak times.

### Viewing Your Schedule

1. Navigate to "Schedule"
2. View your weekly course schedule
3. Check for time conflicts

### Dropping Courses

1. Go to "My Courses"
2. Find the course you want to drop
3. Click "Drop Course"
4. Confirm your action
5. The drop request will be processed (priority over selections)

### Checking Course Information

1. Click "Details" on any course
2. View complete information:
   - Course description
   - Credits and type
   - Schedule
   - Capacity and availability
   - Whether you're enrolled

### Tips for Students

- **Peak Times:** Course selection is busiest at the start of registration. Be patient if there's a queue.
- **Plan Ahead:** Check course schedules for conflicts before selecting.
- **Credit Limits:** Monitor your total credits to stay within requirements.
- **2FA Device:** Keep your authenticator device handy when using the system.
- **Backup Codes:** Save your TOTP secret key in case you lose access to your authenticator.

## Teacher Guide

### Logging In

1. Enter your username and password
2. Click "Login"
3. No 2FA required for teachers

### Managing Your Courses

#### Creating a Course

1. Navigate to "Create Course"
2. Fill in course information:
   - Course name
   - Credits
   - Type (Required/Elective)
   - Location
   - Capacity
   - Schedule (time begin and end)
3. Click "Create"
4. Course will appear in "My Courses"

#### Editing a Course

1. Go to "My Courses"
2. Click "Edit" on the course
3. Modify information
4. Click "Save"

**Note:** Some fields (like capacity) should be edited carefully as students may already be enrolled.

#### Deleting a Course

1. Go to "My Courses"
2. Click "Delete" on the course
3. Confirm deletion

**Warning:** Deleting a course will remove all student enrollments!

### Managing Enrolled Students

#### Viewing Students

1. Go to "My Courses"
2. Click "Details" on a course
3. View list of enrolled students

#### Removing a Student

1. View course details
2. Find the student in the enrollment list
3. Click "Remove"
4. Confirm action

### Course Statistics

View statistics for your courses:
- Total number of courses
- Total enrolled students
- Breakdown by course type

## Administrator Guide

### Logging In

1. Select "Admin Login" tab
2. Enter admin credentials
3. Click "Admin Login"

**Default credentials:**
- Username: `admin`
- Password: `admin123`

**⚠️ IMPORTANT:** Change the default password immediately in production!

### User Management

#### Generating Registration Codes

1. Navigate to "Registration Codes"
2. Select user type (Student/Teacher)
3. Set expiration (1-365 days)
4. Click "Generate Code"
5. Copy and share the code with the user

**Best Practices:**
- Generate codes with short expiration for security
- Keep track of who you give codes to
- Regenerate if a code is compromised

#### Batch User Import

##### From CSV File

1. Prepare CSV file with format:
```csv
username,password,name,email
john.doe,pass123,John Doe,john@example.com
jane.smith,pass456,Jane Smith,jane@example.com
```

2. Run import command:
```bash
python -m backend.common.csv_import users.csv \
  --type student \
  --admin-user admin \
  --admin-pass admin123
```

3. Review import results

##### Generate Random Users

1. Generate users:
```bash
python -m backend.common.user_generator 50 \
  --output students.csv
```

2. Import the generated file

#### Generating 2FA Reset Codes

If a student loses access to their authenticator:

1. Navigate to "Registration Codes"
2. Select "Reset 2FA" option
3. Enter student username
4. Set expiration
5. Click "Generate Reset Code"
6. Share the code with the student

The student can then:
1. Use the reset code to setup new 2FA
2. Scan new QR code
3. Save new secret key

### System Monitoring

#### Check Service Health

```bash
# Check if all services are running
python test_system.py
```

#### View Logs

```bash
# Check service logs
tail -f backend/data_node/*.log
tail -f backend/auth_node/*.log
```

#### Database Backup

```bash
# Backup SQLite databases
cp course_data.db course_data_backup_$(date +%Y%m%d).db
cp auth_data.db auth_data_backup_$(date +%Y%m%d).db
cp queue_data.db queue_data_backup_$(date +%Y%m%d).db
```

### Security Management

#### Change Admin Password

1. Set via environment variable before starting:
```bash
export ADMIN_PASSWORD="your-secure-password"
python -m backend.auth_node.main
```

2. Or update in database directly

#### Configure JWT Secret

```bash
# Generate secure secret
python -c "import secrets; print(secrets.token_urlsafe(32))"

# Set in environment
export JWT_SECRET_KEY="your-generated-secret"
```

#### Monitor Rate Limiting

Check queue statistics:
```bash
curl http://localhost:8005/queue/stats \
  -H "Internal-Token: your-token"
```

### Maintenance Tasks

#### Clear Old Queue Tasks

```bash
# Connect to queue database
sqlite3 queue_data.db

# Delete completed tasks older than 7 days
DELETE FROM queue_tasks 
WHERE status = 'completed' 
AND completed_at < datetime('now', '-7 days');
```

#### Reset User Password

```bash
# Connect to auth database
sqlite3 auth_data.db

# Find user
SELECT * FROM users WHERE username = 'student.name';

# Update password (use hashed password)
# Generate new hash in Python first
```

## FAQ

### General Questions

**Q: What browsers are supported?**
A: Modern browsers including Chrome, Firefox, Safari, and Edge.

**Q: Can I use the system on mobile?**
A: Yes, the interface is responsive and works on mobile devices.

**Q: Is my data secure?**
A: Yes, we use industry-standard encryption and security practices.

### Student Questions

**Q: I lost my authenticator app. What do I do?**
A: Contact your administrator to generate a 2FA reset code.

**Q: Why can't I select more courses?**
A: You may have hit the rate limit. Wait a moment and try again.

**Q: The course is full. Can I get on a waitlist?**
A: Currently there's no waitlist feature. Check back later for availability.

**Q: Can I select the same course multiple times?**
A: No, the system prevents duplicate course selections.

### Teacher Questions

**Q: Can I increase course capacity after students enroll?**
A: Yes, you can edit the capacity at any time.

**Q: How do I export my student list?**
A: Currently, you can view the list in the interface. Export feature coming soon.

**Q: Can I create courses for other teachers?**
A: No, teachers can only manage their own courses.

### Technical Issues

**Q: Services won't start**
A: Check if ports 8001-8005 and 3000 are available. See DEVELOPER.md for troubleshooting.

**Q: 2FA code not working**
A: Ensure your device time is synchronized. Try regenerating the code.

**Q: Rate limit errors**
A: This is normal during peak times. Wait a moment and try again.

**Q: Database errors**
A: Contact your system administrator for assistance.

## Support

For technical support:
- Check documentation in the repository
- Contact system administrator
- Submit an issue on GitHub

## Best Practices

### For Students
- Plan course selections in advance
- Check schedule for conflicts
- Keep authenticator device accessible
- Save backup of secret key
- Respect rate limits

### For Teachers
- Set reasonable course capacities
- Update course information promptly
- Communicate changes to students
- Monitor enrollment regularly

### For Administrators
- Regular database backups
- Monitor system health
- Keep security configs updated
- Rotate registration codes
- Review system logs

---

Need more help? Contact your system administrator or check the developer documentation.
