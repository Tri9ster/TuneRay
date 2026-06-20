#!/usr/bin/env python3
"""
SONOS RAY イコライザー制御スクリプト
低音（Bass）、高音（Treble）、ラウドネス（Loudness）の設定・取得

SONOS RAY Equalizer Control Script
Get/set Bass, Treble, and Loudness settings via the command line.

使用方法 / Usage:
  python sonos_eq_controller.py <ip_address> [command] [value]

例 / Examples:
  python sonos_eq_controller.py 192.168.1.100 set_bass 5
  python sonos_eq_controller.py 192.168.1.100 get_all
  python sonos_eq_controller.py 192.168.1.100 set_treble 3
  python sonos_eq_controller.py 192.168.1.100 set_loudness on
"""

from soco import SoCo, discover
from soco.exceptions import SoCoException
import sys
import argparse
from typing import Optional, Dict, Any


class SonosEQController:
    """SONOS RAYのイコライザー制御クラス / SONOS RAY equalizer controller"""

    def __init__(self, ip_address: Optional[str] = None):
        """
        SonosEQControllerを初期化 / Initialize SonosEQController.

        Args:
            ip_address (str, optional): SONOS デバイスのIPアドレス。指定なしの場合は自動検出
                                        / IP address of the SONOS device. Auto-detected if omitted.

        Raises:
            Exception: デバイスが見つからない場合 / If no device is found or connection fails.
        """
        try:
            if ip_address:
                self.device = SoCo(ip_address)
                # 接続確認 / Verify connection by reading player name
                _ = self.device.player_name
            else:
                # ネットワーク上のSONOSデバイスを自動検出 / Auto-discover SONOS devices on the network
                devices = list(discover())
                if not devices:
                    raise Exception("No Sonos devices found on the network")
                self.device = devices[0]
                print(f"✓ Auto-detected device: {self.device.player_name}")
        except SoCoException as e:
            raise Exception(f"Failed to connect to Sonos device: {e}")
    
    def set_bass(self, value: int) -> bool:
        """
        低音（Bass）を設定 / Set Bass level.

        Args:
            value (int): -10 から 10 の範囲で設定 / Integer in the range -10 to 10.

        Returns:
            bool: 成功時はTrue / True on success.

        Raises:
            ValueError: 範囲外の値が指定された場合 / If the value is out of range.
        """
        if not isinstance(value, int) or not -10 <= value <= 10:
            raise ValueError("Bass value must be an integer between -10 and 10")
        
        try:
            self.device.bass = value
            print(f"✓ Bass set to: {value}")
            return True
        except SoCoException as e:
            print(f"✗ Error setting bass: {e}")
            return False
    
    def get_bass(self) -> Optional[int]:
        """
        現在の低音（Bass）値を取得 / Get the current Bass level.

        Returns:
            int: 現在のBass値（-10〜10）、取得失敗時はNone / Current Bass value (-10 to 10), or None on failure.
        """
        try:
            bass_value = self.device.bass
            print(f"Current Bass: {bass_value}")
            return bass_value
        except SoCoException as e:
            print(f"✗ Error getting bass: {e}")
            return None
    
    def set_treble(self, value: int) -> bool:
        """
        高音（Treble）を設定 / Set Treble level.

        Args:
            value (int): -10 から 10 の範囲で設定 / Integer in the range -10 to 10.

        Returns:
            bool: 成功時はTrue / True on success.

        Raises:
            ValueError: 範囲外の値が指定された場合 / If the value is out of range.
        """
        if not isinstance(value, int) or not -10 <= value <= 10:
            raise ValueError("Treble value must be an integer between -10 and 10")
        
        try:
            self.device.treble = value
            print(f"✓ Treble set to: {value}")
            return True
        except SoCoException as e:
            print(f"✗ Error setting treble: {e}")
            return False
    
    def get_treble(self) -> Optional[int]:
        """
        現在の高音（Treble）値を取得 / Get the current Treble level.

        Returns:
            int: 現在のTreble値（-10〜10）、取得失敗時はNone / Current Treble value (-10 to 10), or None on failure.
        """
        try:
            treble_value = self.device.treble
            print(f"Current Treble: {treble_value}")
            return treble_value
        except SoCoException as e:
            print(f"✗ Error getting treble: {e}")
            return None
    
    def set_loudness(self, enabled: bool) -> bool:
        """
        ラウドネスをON/OFF設定 / Enable or disable Loudness.

        Args:
            enabled (bool): True=ON, False=OFF

        Returns:
            bool: 成功時はTrue / True on success.
        """
        try:
            self.device.loudness = enabled
            status = "ON" if enabled else "OFF"
            print(f"✓ Loudness set to: {status}")
            return True
        except SoCoException as e:
            print(f"✗ Error setting loudness: {e}")
            return False
    
    def get_loudness(self) -> Optional[bool]:
        """
        現在のラウドネス設定を取得 / Get the current Loudness state.

        Returns:
            bool: True=ON, False=OFF、取得失敗時はNone / True=ON, False=OFF, or None on failure.
        """
        try:
            loudness_status = self.device.loudness
            status = "ON" if loudness_status else "OFF"
            print(f"Current Loudness: {status}")
            return loudness_status
        except SoCoException as e:
            print(f"✗ Error getting loudness: {e}")
            return None
    
    def get_all_eq_settings(self) -> Dict[str, Any]:
        """
        すべてのEQ設定を一度に取得 / Fetch all EQ settings in one call.

        Returns:
            dict: bass, treble, loudness の現在値 / Current values for bass, treble, and loudness.
        """
        try:
            settings = {
                'bass': self.device.bass,
                'treble': self.device.treble,
                'loudness': self.device.loudness,
                'device_name': self.device.player_name,
                'ip_address': self.device.ip_address
            }
            return settings
        except SoCoException as e:
            print(f"✗ Error getting EQ settings: {e}")
            return {}
    
    def print_all_eq_settings(self):
        """
        すべてのEQ設定を標準出力に表示 / Print all EQ settings to stdout.
        """
        settings = self.get_all_eq_settings()
        if not settings:
            return
        
        print("\n" + "="*40)
        print("        SONOS EQ Settings")
        print("="*40)
        print(f"Device: {settings.get('device_name', 'N/A')}")
        print(f"IP Address: {settings.get('ip_address', 'N/A')}")
        print(f"Bass: {settings.get('bass', 'N/A')}")
        print(f"Treble: {settings.get('treble', 'N/A')}")
        loudness = settings.get('loudness', None)
        loudness_str = "ON" if loudness else "OFF" if loudness is not None else "N/A"
        print(f"Loudness: {loudness_str}")
        print("="*40 + "\n")


def main():
    """メイン処理 / CLI entry point"""
    parser = argparse.ArgumentParser(
        description='SONOS RAY イコライザー制御スクリプト / SONOS RAY EQ control script',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
例 / Examples:
  %(prog)s 192.168.1.100 set_bass 5
  %(prog)s 192.168.1.100 get_bass
  %(prog)s 192.168.1.100 set_treble 3
  %(prog)s 192.168.1.100 set_loudness on
  %(prog)s 192.168.1.100 get_all
        """
    )
    
    parser.add_argument(
        'ip_address',
        nargs='?',
        default=None,
        help='SONOS デバイスのIPアドレス（省略時は自動検出）/ Device IP address (auto-detected if omitted)',
    )

    parser.add_argument(
        'command',
        nargs='?',
        default='get_all',
        choices=[
            'set_bass', 'get_bass',
            'set_treble', 'get_treble',
            'set_loudness', 'get_loudness',
            'get_all', 'list_devices',
        ],
        help='実行するコマンド / Command to execute',
    )

    parser.add_argument(
        'value',
        nargs='?',
        help='コマンドのパラメータ（bass/treble: -10〜10, loudness: on/off）/ Command parameter (bass/treble: -10 to 10, loudness: on/off)',
    )
    
    args = parser.parse_args()
    
    # list_devices コマンドの場合は特殊処理 / list_devices is handled before connecting to any device
    if args.command == 'list_devices':
        print("\n🔍 Available Sonos Devices:")
        print("-" * 50)
        devices = list(discover())
        if devices:
            for device in devices:
                try:
                    print(f"  • {device.player_name}: {device.ip_address}")
                except:
                    print(f"  • {device.ip_address}")
        else:
            print("  No devices found")
        print("-" * 50 + "\n")
        return
    
    try:
        # コントローラーを初期化 / Initialize controller
        print(f"\n🔊 Connecting to Sonos device...")
        controller = SonosEQController(args.ip_address)

        # コマンドを実行 / Dispatch command
        if args.command == 'set_bass':
            if args.value is None:
                print("Error: set_bass requires a value (-10 to 10)")
                sys.exit(1)
            try:
                value = int(args.value)
                controller.set_bass(value)
            except ValueError as e:
                print(f"Error: {e}")
                sys.exit(1)
        
        elif args.command == 'get_bass':
            controller.get_bass()
        
        elif args.command == 'set_treble':
            if args.value is None:
                print("Error: set_treble requires a value (-10 to 10)")
                sys.exit(1)
            try:
                value = int(args.value)
                controller.set_treble(value)
            except ValueError as e:
                print(f"Error: {e}")
                sys.exit(1)
        
        elif args.command == 'get_treble':
            controller.get_treble()
        
        elif args.command == 'set_loudness':
            if args.value is None:
                print("Error: set_loudness requires a value (on or off)")
                sys.exit(1)
            loudness_value = args.value.lower() in ('on', 'true', '1', 'yes')
            controller.set_loudness(loudness_value)
        
        elif args.command == 'get_loudness':
            controller.get_loudness()
        
        elif args.command == 'get_all':
            controller.print_all_eq_settings()
    
    except Exception as e:
        print(f"\n✗ Error: {e}\n")
        sys.exit(1)
    
    print("✓ Done\n")


if __name__ == "__main__":
    main()
