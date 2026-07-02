import boto3
import json
from pathlib import Path

appconfig = boto3.client('appconfig', region_name='us-east-1')

def update_appconfig():
    """Update AppConfig with new strategy"""
    
    print("="*80)
    print("🔄 UPDATING APPCONFIG WITH NEW STRATEGY")
    print("="*80 + "\n")
    
    # Load updated strategy
    strategy_path = Path("config/model_selection_strategy.json")
    with open(strategy_path, 'r') as f:
        strategy = json.load(f)
    
    print(f"Strategy loaded:")
    print(f"  Primary: {strategy['primary_model']}")
    print(f"  Fallbacks: {strategy['fallback_models']}\n")
    
    # AppConfig IDs (from previous setup)
    app_id = '86x0f23'
    profile_id = 'k8mx8bf'
    
    print(f"App ID: {app_id}")
    print(f"Profile ID: {profile_id}\n")
    
    # Create new configuration version
    print("Creating new configuration version...")
    config_content = json.dumps(strategy, indent=2)
    
    try:
        version_response = appconfig.create_hosted_configuration_version(
            ApplicationId=app_id,
            ConfigurationProfileId=profile_id,
            Description='Updated model selection strategy with correct model IDs',
            Content=config_content,
            ContentType='application/json'
        )
        version_number = version_response['VersionNumber']
        print(f"✅ Configuration version created: {version_number}\n")
    except Exception as e:
        print(f"❌ Error: {e}\n")
        return
    
    # Start deployment
    print("Starting deployment...")
    try:
        deployment = appconfig.start_deployment(
            ApplicationId=app_id,
            EnvironmentId='9261iqe',  # From previous setup
            ConfigurationProfileId=profile_id,
            ConfigurationVersion=str(version_number),
            DeploymentStrategyId='AppConfigAllAtOnce',  # Instant deployment
            Description='Update with corrected model IDs'
        )
        print(f"✅ Deployment started\n")
    except Exception as e:
        print(f"⚠️  Deployment issue: {e}\n")
    
    print("="*80)
    print("✅ APPCONFIG UPDATED!")
    print("="*80)
    print("\nLambda will fetch the updated strategy on next invocation.\n")

if __name__ == "__main__":
    update_appconfig()