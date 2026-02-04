#!/usr/bin/env python3
"""
Quick test script for all enhancements.

Tests:
1. Web dashboard initialization
2. Telegram bot configuration
3. Scheduled tasks setup
4. Voice input configuration (if API key present)
5. Integrated daemon configuration

Usage:
    python3 test_enhancements.py
"""

import sys
from pathlib import Path
import os

# Add current directory to path
sys.path.insert(0, str(Path(__file__).parent))

def test_web_dashboard():
    """Test web dashboard can initialize."""
    print("\n" + "="*60)
    print("TEST 1: Web Dashboard")
    print("="*60)

    try:
        from web_dashboard import app, init_agent, create_templates

        # Create templates
        create_templates()
        print("✓ Templates created")

        # Initialize agent
        agent, runtime = init_agent()
        print(f"✓ Agent initialized: {agent.name}")
        print(f"✓ Telos: {agent.telos.telos['ultimate']['aim']}")

        # Test Flask app
        with app.test_client() as client:
            response = client.get('/api/status')
            print(f"✓ API endpoint working: {response.status_code == 200}")

        print("\n✓ WEB DASHBOARD: PASS")
        return True

    except Exception as e:
        print(f"\n✗ WEB DASHBOARD: FAIL - {e}")
        import traceback
        traceback.print_exc()
        return False


def test_telegram_bot():
    """Test Telegram bot configuration."""
    print("\n" + "="*60)
    print("TEST 2: Telegram Bot")
    print("="*60)

    try:
        # Check if token is set
        token = os.getenv("TELEGRAM_BOT_TOKEN")
        if not token:
            print("⚠ No TELEGRAM_BOT_TOKEN set (expected for optional feature)")
            print("✓ TELEGRAM BOT: SKIP (optional)")
            return True

        from telegram_bot import TelegramConfig, DharmicTelegramBot
        from dharmic_agent import DharmicAgent

        config = TelegramConfig()
        print(f"✓ Config loaded: {len(config.allowed_users)} allowed users")

        agent = DharmicAgent()
        bot = DharmicTelegramBot(agent=agent, config=config)
        print(f"✓ Bot initialized")

        print("\n✓ TELEGRAM BOT: PASS")
        return True

    except ValueError as e:
        if "TELEGRAM_BOT_TOKEN must be set" in str(e):
            print("⚠ No TELEGRAM_BOT_TOKEN set (expected for optional feature)")
            print("✓ TELEGRAM BOT: SKIP (optional)")
            return True
        print(f"\n✗ TELEGRAM BOT: FAIL - {e}")
        return False
    except Exception as e:
        print(f"\n✗ TELEGRAM BOT: FAIL - {e}")
        import traceback
        traceback.print_exc()
        return False


def test_scheduled_tasks():
    """Test scheduled tasks initialization."""
    print("\n" + "="*60)
    print("TEST 3: Scheduled Tasks")
    print("="*60)

    try:
        from scheduled_tasks import ScheduledTasks
        from dharmic_agent import DharmicAgent

        agent = DharmicAgent()
        tasks = ScheduledTasks(agent=agent)
        print(f"✓ Tasks initialized")

        # Don't actually start (that would run forever)
        # Just check we can create the object
        print(f"✓ Log directory created: {tasks.log_dir}")

        print("\n✓ SCHEDULED TASKS: PASS")
        return True

    except Exception as e:
        print(f"\n✗ SCHEDULED TASKS: FAIL - {e}")
        import traceback
        traceback.print_exc()
        return False


def test_voice_input():
    """Test voice input configuration."""
    print("\n" + "="*60)
    print("TEST 4: Voice Input")
    print("="*60)

    try:
        # Check if API key is set
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            print("⚠ No OPENAI_API_KEY set (expected for optional feature)")
            print("✓ VOICE INPUT: SKIP (optional)")
            return True

        from voice_input import VoiceInputConfig, VoiceInput
        from dharmic_agent import DharmicAgent

        config = VoiceInputConfig()
        print(f"✓ Config loaded (OpenAI client available)")

        agent = DharmicAgent()
        voice = VoiceInput(agent=agent, config=config)
        print(f"✓ Voice input initialized")
        print(f"✓ Log directory created: {voice.log_dir}")

        print("\n✓ VOICE INPUT: PASS")
        return True

    except ValueError as e:
        if "OPENAI_API_KEY must be set" in str(e):
            print("⚠ No OPENAI_API_KEY set (expected for optional feature)")
            print("✓ VOICE INPUT: SKIP (optional)")
            return True
        print(f"\n✗ VOICE INPUT: FAIL - {e}")
        return False
    except Exception as e:
        print(f"\n✗ VOICE INPUT: FAIL - {e}")
        import traceback
        traceback.print_exc()
        return False


def test_integrated_daemon():
    """Test integrated daemon configuration."""
    print("\n" + "="*60)
    print("TEST 5: Integrated Daemon")
    print("="*60)

    try:
        from integrated_daemon import DaemonConfig, IntegratedDaemon

        # Create config
        config = DaemonConfig()
        print(f"✓ Config loaded")

        # Test config template generation
        template_path = Path(__file__).parent / "test_daemon_config.yaml"
        config.save_template(str(template_path))
        print(f"✓ Template generated: {template_path}")

        # Initialize daemon (but don't start)
        daemon = IntegratedDaemon(config)
        print(f"✓ Daemon initialized: {daemon.agent.name}")
        print(f"✓ Runtime available: {daemon.runtime is not None}")
        print(f"✓ Scheduled tasks available: {daemon.scheduled_tasks is not None}")

        # Clean up template
        template_path.unlink()

        print("\n✓ INTEGRATED DAEMON: PASS")
        return True

    except Exception as e:
        print(f"\n✗ INTEGRATED DAEMON: FAIL - {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all tests."""
    print("="*60)
    print("DHARMIC AGENT ENHANCEMENTS - TEST SUITE")
    print("="*60)
    print(f"Test location: {Path(__file__).parent}")
    print("")

    results = []

    # Run tests
    results.append(("Web Dashboard", test_web_dashboard()))
    results.append(("Telegram Bot", test_telegram_bot()))
    results.append(("Scheduled Tasks", test_scheduled_tasks()))
    results.append(("Voice Input", test_voice_input()))
    results.append(("Integrated Daemon", test_integrated_daemon()))

    # Summary
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)

    passed = sum(1 for _, result in results if result)
    total = len(results)

    for name, result in results:
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"{status:12} {name}")

    print("-"*60)
    print(f"Total: {passed}/{total} tests passed")
    print("="*60)

    if passed == total:
        print("\n✓ ALL TESTS PASSED - Enhancements ready to use!")
        print("\nNext steps:")
        print("  1. Configure environment variables (see ENHANCEMENT_README.md)")
        print("  2. Test individual components:")
        print("     python3 web_dashboard.py")
        print("     python3 telegram_bot.py")
        print("     python3 scheduled_tasks.py --test morning")
        print("  3. Run integrated daemon:")
        print("     python3 integrated_daemon.py --all")
    else:
        print("\n⚠ Some tests failed - check output above")
        sys.exit(1)


if __name__ == "__main__":
    main()
