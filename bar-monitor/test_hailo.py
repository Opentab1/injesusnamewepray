#!/usr/bin/env python3
"""
Hailo Installation Test Script

Run this to verify your Hailo HAT is properly installed and working.

Usage: python3 test_hailo.py
"""

import subprocess
import sys
from pathlib import Path
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def print_header(text):
    """Print a formatted header."""
    print("\n" + "=" * 60)
    print(text)
    print("=" * 60)


def check_hailo_device():
    """Check if Hailo device is detected."""
    print_header("1. Checking Hailo Device")
    
    try:
        result = subprocess.run(
            ['hailortcli', 'fw-control', 'identify'],
            capture_output=True,
            text=True,
            timeout=10
        )
        
        if result.returncode == 0:
            print("✓ Hailo device detected!")
            print("\nDevice Information:")
            print(result.stdout)
            return True
        else:
            print("✗ Hailo device not detected")
            print(f"Error: {result.stderr}")
            return False
    
    except FileNotFoundError:
        print("✗ 'hailortcli' command not found")
        print("\nHailo software not installed. Install with:")
        print("  sudo apt update")
        print("  sudo apt install hailo-all")
        return False
    
    except subprocess.TimeoutExpired:
        print("✗ Command timed out - device may not be connected")
        return False
    
    except Exception as e:
        print(f"✗ Error: {e}")
        return False


def check_hailo_examples():
    """Check if hailo-rpi5-examples is installed."""
    print_header("2. Checking hailo-rpi5-examples")
    
    possible_paths = [
        Path.home() / "hailo-rpi5-examples",
        Path("/home/ubuntu/hailo-rpi5-examples"),
        Path.cwd() / "hailo-rpi5-examples",
    ]
    
    for path in possible_paths:
        if path.exists():
            print(f"✓ Found at: {path}")
            
            # Check for key files
            detection_script = path / "basic_pipelines" / "detection.py"
            if detection_script.exists():
                print("✓ detection.py found")
            else:
                print("✗ detection.py not found - run ./install.sh")
                return False
            
            return True
    
    print("✗ hailo-rpi5-examples not found")
    print("\nInstall with:")
    print("  cd ~")
    print("  git clone https://github.com/hailo-ai/hailo-rpi5-examples.git")
    print("  cd hailo-rpi5-examples")
    print("  ./install.sh")
    return False


def check_camera():
    """Check if camera is available."""
    print_header("3. Checking Camera")
    
    # Check for video devices
    video_devices = list(Path("/dev").glob("video*"))
    
    if video_devices:
        print(f"✓ Found {len(video_devices)} video device(s):")
        for dev in video_devices:
            print(f"  - {dev}")
        return True
    else:
        print("✗ No video devices found")
        print("\nMake sure:")
        print("  1. Pi Camera is connected (if using Pi Camera)")
        print("  2. USB camera is plugged in (if using USB camera)")
        print("  3. Camera is enabled in raspi-config")
        return False


def check_python_packages():
    """Check if required Python packages are available."""
    print_header("4. Checking Python Packages")
    
    required_packages = [
        ('numpy', 'numpy'),
        ('cv2', 'opencv-python'),
        ('yaml', 'PyYAML'),
    ]
    
    all_ok = True
    
    for import_name, package_name in required_packages:
        try:
            __import__(import_name)
            print(f"✓ {package_name}")
        except ImportError:
            print(f"✗ {package_name} not installed")
            all_ok = False
    
    if not all_ok:
        print("\nInstall missing packages with:")
        print("  pip3 install numpy opencv-python PyYAML")
    
    return all_ok


def check_gstreamer():
    """Check if GStreamer is available."""
    print_header("5. Checking GStreamer")
    
    try:
        result = subprocess.run(
            ['gst-inspect-1.0', '--version'],
            capture_output=True,
            text=True,
            timeout=5
        )
        
        if result.returncode == 0:
            print("✓ GStreamer installed")
            version_line = result.stdout.split('\n')[0]
            print(f"  {version_line}")
            return True
        else:
            print("✗ GStreamer not working")
            return False
    
    except FileNotFoundError:
        print("✗ GStreamer not installed")
        print("\nInstall with:")
        print("  sudo apt install gstreamer1.0-tools gstreamer1.0-plugins-base")
        return False
    
    except Exception as e:
        print(f"✗ Error: {e}")
        return False


def run_quick_test():
    """Run a quick detection test if everything is installed."""
    print_header("6. Quick Detection Test")
    
    hailo_path = None
    for path in [Path.home() / "hailo-rpi5-examples", 
                 Path("/home/ubuntu/hailo-rpi5-examples")]:
        if path.exists():
            hailo_path = path
            break
    
    if not hailo_path:
        print("✗ Cannot run test - hailo-rpi5-examples not found")
        return False
    
    print("To run a manual test, execute these commands:")
    print(f"\n  cd {hailo_path}")
    print("  source setup_env.sh")
    print("  python basic_pipelines/detection.py --input rpi")
    print("\nThis will open a window showing real-time detection.")
    print("Press Ctrl+C to stop.")
    
    return True


def main():
    """Run all tests."""
    print("""
╔═══════════════════════════════════════════════════════════╗
║                                                           ║
║           HAILO HAT INSTALLATION TEST                     ║
║                                                           ║
║  This script checks if your Hailo HAT is properly        ║
║  installed and ready to use.                              ║
║                                                           ║
╚═══════════════════════════════════════════════════════════╝
    """)
    
    # Run all checks
    results = {
        'Hailo Device': check_hailo_device(),
        'Hailo Examples': check_hailo_examples(),
        'Camera': check_camera(),
        'Python Packages': check_python_packages(),
        'GStreamer': check_gstreamer(),
    }
    
    # Run quick test if everything passed
    if all(results.values()):
        run_quick_test()
    
    # Summary
    print_header("Test Summary")
    
    for test_name, passed in results.items():
        status = "✓ PASS" if passed else "✗ FAIL"
        print(f"{test_name:.<30} {status}")
    
    print()
    
    if all(results.values()):
        print("🎉 All tests passed! Your Hailo HAT is ready to use.")
        print("\nNext steps:")
        print("  1. Adjust settings in config/settings.yaml")
        print("  2. Run: python3 main.py")
        return 0
    else:
        print("⚠ Some tests failed. Please fix the issues above.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
