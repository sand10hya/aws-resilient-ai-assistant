import boto3
import json
from pathlib import Path

appconfig = boto3.client('appconfig', region_name='us-east-1')

def setup_appconfig():
    """Set up AWS AppConfig for dynamic model selection"""
    
    print("🔧 Setting up AWS AppConfig...\n")
    
    # Load model selection strategy
    strategy_path = Path("config/model_selection_strategy.json")
    with open(strategy_path, 'r') as f:
        strategy = json.load(f)
    
    print(f"Strategy loaded: Primary model = {strategy['primary_model']}\n")
    
    # Step 1: Create Application
    print("Step 1: Creating AppConfig Application...")
    try:
        app_response = appconfig.create_application(
            Name='AIAssistantApp',
            Description='AI Assistant Application Configuration'
        )
        app_id = app_response['Id']
        print(f"✅ Application created: {app_id}\n")
    except appconfig.exceptions.ResourceInUseException:
        print("⚠️  Application already exists, fetching...\n")
        apps = appconfig.list_applications()['Items']
        app_id = next((app['Id'] for app in apps if app['Name'] == 'AIAssistantApp'), None)
        if not app_id:
            print("❌ Could not find application")
            return
    
    # Step 2: Create Environment
    print("Step 2: Creating Environment...")
    try:
        env_response = appconfig.create_environment(
            ApplicationId=app_id,
            Name='Production',
            Description='Production environment'
        )
        env_id = env_response['Id']
        print(f"✅ Environment created: {env_id}\n")
    except appconfig.exceptions.ResourceInUseException:
        print("⚠️  Environment already exists\n")
        envs = appconfig.list_environments(ApplicationId=app_id)['Items']
        env_id = next((e['Id'] for e in envs if e['Name'] == 'Production'), None)
    
    # Step 3: Create Configuration Profile
    print("Step 3: Creating Configuration Profile...")
    try:
        profile_response = appconfig.create_configuration_profile(
            ApplicationId=app_id,
            Name='ModelSelectionStrategy',
            Description='Model selection strategy for AI Assistant',
            LocationUri='hosted'
        )
        profile_id = profile_response['Id']
        print(f"✅ Configuration Profile created: {profile_id}\n")
    except appconfig.exceptions.ResourceInUseException:
        print("⚠️  Configuration Profile already exists\n")
        profiles = appconfig.list_configuration_profiles(ApplicationId=app_id)['Items']
        profile_id = next((p['Id'] for p in profiles if p['Name'] == 'ModelSelectionStrategy'), None)
    
    # Step 4: Create Hosted Configuration Version
    print("Step 4: Uploading Configuration...")
    config_content = json.dumps(strategy, indent=2)
    try:
        version_response = appconfig.create_hosted_configuration_version(
            ApplicationId=app_id,
            ConfigurationProfileId=profile_id,
            Description='Initial model selection strategy',
            Content=config_content,
            ContentType='application/json'
        )
        version_number = version_response['VersionNumber']
        print(f"✅ Configuration version created: {version_number}\n")
    except Exception as e:
        print(f"Error creating configuration version: {e}\n")
        return
    
    # Step 5: Create Deployment Strategy
    print("Step 5: Creating Deployment Strategy...")
    try:
        strategy_response = appconfig.create_deployment_strategy(
            Name='AIAssistantDeploymentStrategy',
            Description='Quick deployment for testing',
            DeploymentDurationInMinutes=0,
            FinalBakeTimeInMinutes=0,
            GrowthFactor=100.0,
            GrowthType='EXPONENTIAL_LINEAR'
        )
        deployment_strategy_id = strategy_response['Id']
        print(f"✅ Deployment Strategy created: {deployment_strategy_id}\n")
    except appconfig.exceptions.ResourceInUseException:
        print("⚠️  Deployment Strategy already exists\n")
        strategies = appconfig.list_deployment_strategies()['Items']
        deployment_strategy_id = next((s['Id'] for s in strategies if s['Name'] == 'AIAssistantDeploymentStrategy'), None)
    
    # Step 6: Start Deployment
    print("Step 6: Starting Deployment...")
    try:
        deployment_response = appconfig.start_deployment(
            ApplicationId=app_id,
            EnvironmentId=env_id,
            ConfigurationProfileId=profile_id,
            ConfigurationVersion=str(version_number),
            DeploymentStrategyId=deployment_strategy_id,
            Description='Initial deployment'
        )
        deployment_id = deployment_response['DeploymentNumber']
        print(f"✅ Deployment started: {deployment_id}\n")
    except Exception as e:
        print(f"⚠️  Deployment error: {e}\n")
    
    # Print summary
    print("="*80)
    print("✅ AppConfig Setup Complete!")
    print("="*80)
    print(f"\nApplication ID: {app_id}")
    print(f"Environment ID: {env_id}")
    print(f"Configuration Profile ID: {profile_id}")
    print(f"\nModel Strategy:")
    print(f"  Primary: {strategy['primary_model']}")
    print(f"  Fallback: {strategy['fallback_models']}")
    print("\nTo update model strategy:")
    print("1. Go to AWS Console → AppConfig")
    print("2. Select 'AIAssistantApp'")
    print("3. Go to 'ModelSelectionStrategy' configuration")
    print("4. Edit and deploy new version")
    print("5. Lambda will fetch updated config automatically!")
    print("\n" + "="*80)
    
    # Save AppConfig info
    appconfig_info = {
        "application_id": app_id,
        "environment_id": env_id,
        "configuration_profile_id": profile_id,
        "deployment_strategy_id": deployment_strategy_id,
        "strategy": strategy
    }
    
    with open('config/appconfig_info.json', 'w') as f:
        json.dump(appconfig_info, f, indent=2)
    
    print("✅ AppConfig info saved to config/appconfig_info.json\n")

if __name__ == "__main__":
    setup_appconfig()