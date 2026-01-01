"""Import SQL schema to Supabase database using pg8000."""
import os
import pg8000.native

# Read environment variables
with open('.env', 'r', encoding='utf-8') as f:
    for line in f:
        line = line.strip()
        if line and not line.startswith('#') and '=' in line:
            key, value = line.split('=', 1)
            os.environ[key] = value

# Read the SQL schema file
with open("packages/core/migrations/001_initial_schema.sql", "r", encoding="utf-8") as f:
    schema_sql = f.read()

# Try direct connection first, fall back to pooler
database_url = os.environ.get("DATABASE_DIRECT_URL")
if not database_url or 'direct' not in os.environ:
    database_url = os.environ.get("DATABASE_URL")
if not database_url:
    print("❌ DATABASE_URL not found in environment")
    exit(1)

print("=" * 80)
print("Importing SQL Schema to Supabase")
print("=" * 80)

# Parse database URL
# Format: postgresql://postgres.project:[PASSWORD]@host:port/database
try:
    url_parts = database_url.replace('postgresql://', '').split('@')
    auth_part = url_parts[0]
    host_part = url_parts[1]
    
    username = auth_part.split(':')[0]
    password = auth_part.split(':')[1].strip('[]')
    host = host_part.split(':')[0]
    port = int(host_part.split(':')[1].split('/')[0])
    database = host_part.split('/')[1] if '/' in host_part else 'postgres'
    
    # For pooler connections, we need to specify the database in the username
    # Format: postgres.project_ref
    if 'pooler' in host:
        print(f"Using pooler connection")
        print(f"Host: {host}")
        print(f"Database: {database}")
        print()
    else:
        print(f"Using direct connection")
        print(f"Host: {host}")
        print(f"Database: {database}")
        print()
    
    print("Connecting to database...")
    
    # For pooler, strip the brackets from password
    clean_password = password.replace('[', '').replace(']', '')
    
    # Connection parameters
    connect_params = {
        'user': username,
        'password': clean_password,
        'host': host,
        'port': port,
        'database': database,
        'ssl_context': True
    }
    
    # For pooler connections, add options for session mode
    if 'pooler' in host:
        print("Using pooler with options...")
        connect_params['options'] = '-c statement_timeout=300000'
    
    # Try connection with proper parameters
    conn = pg8000.native.Connection(**connect_params)
    
    print("✅ Connected successfully!")
    print("Executing schema...")
    
    # Execute SQL
    conn.run(schema_sql)
    
    conn.close()
    
    print()
    print("✅ Schema imported successfully!")
    print("=" * 80)
    
except Exception as e:
    print(f"❌ Error: {e}")
    print()
    print("=" * 80)
    print()
    print("I need the DIRECT connection string (not pooler) from Supabase.")
    print()
    print("Please provide:")
    print("1. Go to: https://supabase.com/dashboard/project/wmyldpegqudnzoxpudmv/settings/database")
    print("2. Find 'Connection string' section")
    print("3. Copy the 'URI' or 'Direct connection' string")
    print("4. It should look like: postgresql://postgres:[PASSWORD]@db.wmyldpegqudnzoxpudmv.supabase.co:6543/postgres")
    print()
    print("Add it to your .env file as:")
    print("DATABASE_DIRECT_URL=<paste the connection string here>")
    print()
    exit(1)
