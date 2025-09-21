# Database Schema
CREATE TABLE settings (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL
);

# Database connection string
db_connection_string = "postgresql://admin:admin@localhost/db"

# Name of the settings table
settings_table_name = "settings"

# Create an instance of the SettingsManager
settings_manager = SettingsManager(db_connection_string, settings_table_name)

# Set some settings
settings_manager.set("app_name", "MyApplication")
settings_manager.set("max_connections", "10")
settings_manager.set("feature_enabled", "true")

# Get settings
app_name = settings_manager.get("app_name")
max_connections = settings_manager.get_int("max_connections")
feature_enabled = settings_manager.get_bool("feature_enabled")

print(f"App Name: {app_name}")
print(f"Max Connections: {max_connections}")
print(f"Feature Enabled: {feature_enabled}")

# Validate a key
try:
    settings_manager.validate_key("valid_key_123")
    print("Key is valid")
except ValueError as e:
    print(f"Key validation error: {e}")

# Reload settings from the database
settings_manager.reload()

# Get a setting after reload
app_name_after_reload = settings_manager.get("app_name")
print(f"App Name after reload: {app_name_after_reload}")
