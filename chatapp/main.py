import json
import os
import re
import asyncio

import requests
from kivymd.app import MDApp
from kivymd.uix.screenmanager import MDScreenManager
from kivymd.uix.screen import MDScreen
from kivymd.uix.textfield import MDTextField
from kivymd.uix.button import MDButton, MDButtonText
from kivymd.uix.label import MDLabel
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.scrollview import ScrollView
from kivy.uix.widget import Widget
from kivy.graphics import Color, Rectangle
from kivy.metrics import dp
from kivy.core.text import LabelBase
from nio import AsyncClient, LoginResponse, RegisterResponse, RoomMessageText, SyncResponse

from user_store import add_user, is_superuser, list_users, set_superuser

THEME_PATH = os.path.join(os.path.dirname(__file__), "themes", "default.json")
AVAILABLE_COLORS = ["Blue", "Red", "Green", "Purple", "Orange", "Teal"]

COLOR_RGB = {
    "Blue": (0.13, 0.35, 0.95),
    "Red": (0.85, 0.15, 0.15),
    "Green": (0.15, 0.65, 0.25),
    "Purple": (0.55, 0.2, 0.85),
    "Orange": (0.95, 0.5, 0.1),
    "Teal": (0.1, 0.6, 0.6),
}


def load_theme():
    with open(THEME_PATH, "r") as f:
        return json.load(f)


def save_theme(theme):
    with open(THEME_PATH, "w") as f:
        json.dump(theme, f, indent=2)


class GradientBackground(Widget):
    def __init__(self, top_color=(0.1, 0.1, 0.15, 1), bottom_color=(0.05, 0.05, 0.08, 1), **kwargs):
        super().__init__(**kwargs)
        self.top_color = top_color
        self.bottom_color = bottom_color
        self.bind(pos=self.redraw, size=self.redraw)
        self.redraw()

    def redraw(self, *args):
        self.canvas.before.clear()
        steps = 40
        with self.canvas.before:
            for i in range(steps):
                t = i / steps
                r = self.top_color[0] + (self.bottom_color[0] - self.top_color[0]) * t
                g = self.top_color[1] + (self.bottom_color[1] - self.top_color[1]) * t
                b = self.top_color[2] + (self.bottom_color[2] - self.top_color[2]) * t
                Color(r, g, b, 1)
                Rectangle(
                    pos=(self.x, self.y + self.height * (1 - (i + 1) / steps)),
                    size=(self.width, self.height / steps + 1),
                )


class LoginScreen(MDScreen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.name = "login"
        layout = BoxLayout(
            orientation="vertical", spacing=dp(16), padding=dp(32),
            size_hint=(0.8, 0.6), pos_hint={"center_x": 0.5, "center_y": 0.5},
        )
        self.status_label = MDLabel(text="Enter your credentials", halign="center")
        self.username_field = MDTextField(hint_text="Username")
        self.password_field = MDTextField(hint_text="Password", password=True)
        self.server_field = MDTextField(hint_text="Homeserver URL", text="http://localhost:8008")
        login_button = MDButton(MDButtonText(text="Login"), style="filled")
        login_button.bind(on_release=self.try_login)
        register_button = MDButton(MDButtonText(text="Sign up"), style="text")
        register_button.bind(on_release=self.go_to_register)
        for w in (self.status_label, self.server_field, self.username_field, self.password_field, login_button, register_button):
            layout.add_widget(w)
        self.add_widget(layout)

    def go_to_register(self, *args):
        MDApp.get_running_app().root.current = "register"

    def try_login(self, *args):
        self.status_label.text = "wait a few seconds"
        asyncio.create_task(self.do_login(self.server_field.text, self.username_field.text, self.password_field.text))

    async def do_login(self, server, username, password):
        app = MDApp.get_running_app()
        client = AsyncClient(server, username)
        resp = await client.login(password)
        if isinstance(resp, LoginResponse):
            app.client = client
            app.current_username = username
            if is_superuser(username):
                self.status_label.text = f"Logged in as {resp.user_id} (admin)"
                app.root.current = "admin"
                return
            self.status_label.text = f"Logged in as {resp.user_id}"
            app.root.get_screen("rooms").load_rooms()
            app.root.current = "rooms"
            app.start_sync_loop()
        else:
            self.status_label.text = f"Login failed: {resp}"


class RegisterScreen(MDScreen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.name = "register"
        layout = BoxLayout(
            orientation="vertical", spacing=dp(16), padding=dp(32),
            size_hint=(0.8, 0.6), pos_hint={"center_x": 0.5, "center_y": 0.5},
        )
        self.status_label = MDLabel(text="Create an account", halign="center")
        self.username_field = MDTextField(hint_text="Choose a username")
        self.password_field = MDTextField(hint_text="Choose a password", password=True)
        self.confirm_field = MDTextField(hint_text="Confirm password", password=True)
        self.server_field = MDTextField(hint_text="Homeserver URL", text="http://localhost:8008")
        register_button = MDButton(MDButtonText(text="Create account"), style="filled")
        register_button.bind(on_release=self.try_register)
        back_button = MDButton(MDButtonText(text="Back to login screen"), style="text")
        back_button.bind(on_release=self.go_back)
        for w in (self.status_label, self.server_field, self.username_field,
                  self.password_field, self.confirm_field, register_button, back_button):
            layout.add_widget(w)
        self.add_widget(layout)

    def go_back(self, *args):
        MDApp.get_running_app().root.current = "login"

    def try_register(self, *args):
        username = self.username_field.text.strip()
        password = self.password_field.text
        confirm = self.confirm_field.text
        server = self.server_field.text.strip()
        if not username or not password:
            self.status_label.text = "Username and password required"
            return
        if password != confirm:
            self.status_label.text = "Passwords don't match"
            return
        self.status_label.text = "Creating account..."
        asyncio.create_task(self.do_register(server, username, password))

    async def do_register(self, server, username, password):
        client = AsyncClient(server, username)
        resp = await client.register(username, password, device_name="chatapp")
        if isinstance(resp, RegisterResponse):
            add_user(username, password, is_superuser=False)
            self.status_label.text = f"Account created: {resp.user_id}. You can log in now."
            await client.close()
            login_screen = MDApp.get_running_app().root.get_screen("login")
            login_screen.username_field.text = username
            login_screen.server_field.text = server
            login_screen.status_label.text = "Account created — log in below"
            MDApp.get_running_app().root.current = "login"
        else:
            self.status_label.text = f"Registration failed: {resp}"
            await client.close()


class NewChatScreen(MDScreen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.name = "new_chat"
        layout = BoxLayout(
            orientation="vertical", spacing=dp(16), padding=dp(32),
            size_hint=(0.8, 0.5), pos_hint={"center_x": 0.5, "center_y": 0.5},
        )
        self.status_label = MDLabel(text="Start a chat with a friend", halign="center")
        self.user_id_field = MDTextField(hint_text="@friend:localhost")
        start_button = MDButton(MDButtonText(text="Start chat"), style="filled")
        start_button.bind(on_release=self.start_chat)
        back_button = MDButton(MDButtonText(text="Back"), style="text")
        back_button.bind(on_release=self.go_back)
        for w in (self.status_label, self.user_id_field, start_button, back_button):
            layout.add_widget(w)
        self.add_widget(layout)

    def go_back(self, *args):
        MDApp.get_running_app().root.current = "rooms"

    def start_chat(self, *args):
        user_id = self.user_id_field.text.strip()
        if not user_id.startswith("@") or ":" not in user_id:
            self.status_label.text = "Enter a full Matrix ID, e.g. @friend:localhost"
            return
        self.status_label.text = "Starting chat..."
        asyncio.create_task(self._start_chat(user_id))

    async def _start_chat(self, user_id):
        app = MDApp.get_running_app()
        resp = await app.client.room_create(invite=[user_id], is_direct=True)
        self.status_label.text = f"Chat started: {resp}"
        app.root.get_screen("rooms").load_rooms()
        app.root.current = "rooms"


class NewGroupScreen(MDScreen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.name = "new_group"
        layout = BoxLayout(
            orientation="vertical", spacing=dp(16), padding=dp(32),
            size_hint=(0.8, 0.6), pos_hint={"center_x": 0.5, "center_y": 0.5},
        )
        self.status_label = MDLabel(text="Create a group", halign="center")
        self.name_field = MDTextField(hint_text="Group name")
        self.members_field = MDTextField(hint_text="Members, comma-separated (@a:localhost, @b:localhost)")
        create_button = MDButton(MDButtonText(text="Create group"), style="filled")
        create_button.bind(on_release=self.create_group)
        back_button = MDButton(MDButtonText(text="Back"), style="text")
        back_button.bind(on_release=self.go_back)
        for w in (self.status_label, self.name_field, self.members_field, create_button, back_button):
            layout.add_widget(w)
        self.add_widget(layout)

    def go_back(self, *args):
        MDApp.get_running_app().root.current = "rooms"

    def create_group(self, *args):
        name = self.name_field.text.strip()
        members_raw = self.members_field.text.strip()
        if not name:
            self.status_label.text = "Group needs a name"
            return
        members = [m.strip() for m in members_raw.split(",") if m.strip()]
        self.status_label.text = "Creating group..."
        asyncio.create_task(self._create_group(name, members))

    async def _create_group(self, name, members):
        app = MDApp.get_running_app()
        resp = await app.client.room_create(name=name, invite=members)
        self.status_label.text = f"Group created: {resp}"
        app.root.get_screen("rooms").load_rooms()
        app.root.current = "rooms"


class RoomListScreen(MDScreen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.name = "rooms"
        outer = BoxLayout(orientation="vertical")
        top_bar = BoxLayout(orientation="horizontal", size_hint_y=None, height=dp(48), padding=dp(8), spacing=dp(4))
        settings_button = MDButton(MDButtonText(text="Theme"), style="text")
        settings_button.bind(on_release=self.open_theme_settings)
        new_chat_button = MDButton(MDButtonText(text="New chat"), style="text")
        new_chat_button.bind(on_release=self.open_new_chat)
        new_group_button = MDButton(MDButtonText(text="New group"), style="text")
        new_group_button.bind(on_release=self.open_new_group)
        for b in (settings_button, new_chat_button, new_group_button):
            top_bar.add_widget(b)
        self.layout = BoxLayout(orientation="vertical", spacing=dp(8), padding=dp(16), size_hint_y=None)
        self.layout.bind(minimum_height=self.layout.setter("height"))
        scroll = ScrollView()
        scroll.add_widget(self.layout)
        outer.add_widget(top_bar)
        outer.add_widget(scroll)
        self.add_widget(outer)

    def open_theme_settings(self, *args):
        MDApp.get_running_app().root.current = "theme_settings"

    def open_new_chat(self, *args):
        MDApp.get_running_app().root.current = "new_chat"

    def open_new_group(self, *args):
        MDApp.get_running_app().root.current = "new_group"

    def load_rooms(self):
        asyncio.create_task(self._load_rooms())

    async def _load_rooms(self):
        app = MDApp.get_running_app()
        await app.client.sync(timeout=30000)
        self.refresh_room_buttons()

    def refresh_room_buttons(self):
        app = MDApp.get_running_app()
        self.layout.clear_widgets()
        for room_id, room_info in app.client.rooms.items():
            btn = MDButton(MDButtonText(text=room_info.display_name or room_id), style="outlined")
            btn.room_id = room_id
            btn.bind(on_release=self.open_room)
            self.layout.add_widget(btn)

    def open_room(self, instance):
        app = MDApp.get_running_app()
        chat_screen = app.root.get_screen("chat")
        chat_screen.room_id = instance.room_id
        chat_screen.load_messages()
        app.root.current = "chat"


class ThemeSettingsScreen(MDScreen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.name = "theme_settings"
        outer = BoxLayout(orientation="vertical", padding=dp(16), spacing=dp(12))
        back_button = MDButton(MDButtonText(text="Back"), style="text")
        back_button.bind(on_release=self.go_back)
        outer.add_widget(back_button)
        outer.add_widget(MDLabel(text="Pick a primary color", halign="center", size_hint_y=None, height=dp(40)))
        color_grid = BoxLayout(orientation="vertical", spacing=dp(8), size_hint_y=None)
        color_grid.bind(minimum_height=color_grid.setter("height"))
        for color in AVAILABLE_COLORS:
            btn = MDButton(MDButtonText(text=color), style="outlined")
            btn.color_name = color
            btn.bind(on_release=self.pick_color)
            color_grid.add_widget(btn)
        outer.add_widget(color_grid)

        gradient_btn = MDButton(MDButtonText(text="Toggle gradient background"), style="outlined")
        gradient_btn.bind(on_release=self.toggle_gradient)
        outer.add_widget(gradient_btn)

        glow_btn = MDButton(MDButtonText(text="Toggle mention glow effect"), style="outlined")
        glow_btn.bind(on_release=self.toggle_glow)
        outer.add_widget(glow_btn)

        self.status_label = MDLabel(text="", halign="center", size_hint_y=None, height=dp(30))
        outer.add_widget(self.status_label)
        self.add_widget(outer)

    def pick_color(self, instance):
        app = MDApp.get_running_app()
        app.theme["primary_color"] = instance.color_name
        app.theme_cls.primary_palette = instance.color_name
        save_theme(app.theme)
        self.status_label.text = f"Theme set to {instance.color_name} (saved)"

    def toggle_gradient(self, instance):
        app = MDApp.get_running_app()
        app.theme["use_gradient"] = not app.theme.get("use_gradient", False)
        save_theme(app.theme)
        self.status_label.text = f"Gradient background: {'ON' if app.theme['use_gradient'] else 'OFF'} (restart app to see it)"

    def toggle_glow(self, instance):
        app = MDApp.get_running_app()
        app.theme["overlay_glow"] = not app.theme.get("overlay_glow", True)
        save_theme(app.theme)
        self.status_label.text = f"Mention glow: {'ON' if app.theme['overlay_glow'] else 'OFF'}"

    def go_back(self, *args):
        MDApp.get_running_app().root.current = "rooms"


class AdminScreen(MDScreen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.name = "admin"
        outer = BoxLayout(orientation="vertical", padding=dp(16), spacing=dp(12), size_hint_y=None)
        outer.bind(minimum_height=outer.setter("height"))
        scroll_outer = ScrollView()
        scroll_outer.add_widget(outer)

        outer.add_widget(MDLabel(text="Admin Dashboard", halign="center", size_hint_y=None, height=dp(40)))

        outer.add_widget(MDLabel(text="Register new user", halign="center", size_hint_y=None, height=dp(30)))
        reg_row = BoxLayout(orientation="horizontal", size_hint_y=None, height=dp(56), spacing=dp(8))
        self.new_username_field = MDTextField(hint_text="Username")
        self.new_password_field = MDTextField(hint_text="Password", password=True)
        reg_button = MDButton(MDButtonText(text="Create"), style="filled")
        reg_button.bind(on_release=self.register_user)
        reg_row.add_widget(self.new_username_field)
        reg_row.add_widget(self.new_password_field)
        reg_row.add_widget(reg_button)
        outer.add_widget(reg_row)

        outer.add_widget(MDLabel(text="Users", halign="center", size_hint_y=None, height=dp(30)))
        self.user_list_layout = BoxLayout(orientation="vertical", spacing=dp(8), size_hint_y=None)
        self.user_list_layout.bind(minimum_height=self.user_list_layout.setter("height"))
        outer.add_widget(self.user_list_layout)

        outer.add_widget(MDLabel(text="Reset a user's password", halign="center", size_hint_y=None, height=dp(30)))
        reset_row = BoxLayout(orientation="horizontal", size_hint_y=None, height=dp(56), spacing=dp(8))
        self.reset_username_field = MDTextField(hint_text="Username")
        self.reset_password_field = MDTextField(hint_text="New password", password=True)
        reset_button = MDButton(MDButtonText(text="Reset"), style="filled")
        reset_button.bind(on_release=self.reset_password)
        reset_row.add_widget(self.reset_username_field)
        reset_row.add_widget(self.reset_password_field)
        reset_row.add_widget(reset_button)
        outer.add_widget(reset_row)

        outer.add_widget(MDLabel(text="Kick / ban from a room", halign="center", size_hint_y=None, height=dp(30)))
        room_mod_row = BoxLayout(orientation="horizontal", size_hint_y=None, height=dp(56), spacing=dp(8))
        self.mod_room_field = MDTextField(hint_text="Room ID (!abc:localhost)")
        self.mod_user_field = MDTextField(hint_text="User (@name:localhost)")
        kick_button = MDButton(MDButtonText(text="Kick"), style="outlined")
        kick_button.bind(on_release=self.kick_user)
        ban_button = MDButton(MDButtonText(text="Ban"), style="outlined")
        ban_button.bind(on_release=self.ban_user)
        room_mod_row.add_widget(self.mod_room_field)
        room_mod_row.add_widget(self.mod_user_field)
        room_mod_row.add_widget(kick_button)
        room_mod_row.add_widget(ban_button)
        outer.add_widget(room_mod_row)

        outer.add_widget(MDLabel(text="Delete a message", halign="center", size_hint_y=None, height=dp(30)))
        redact_row = BoxLayout(orientation="horizontal", size_hint_y=None, height=dp(56), spacing=dp(8))
        self.redact_room_field = MDTextField(hint_text="Room ID")
        self.redact_event_field = MDTextField(hint_text="Event ID ($abc...)")
        redact_button = MDButton(MDButtonText(text="Delete message"), style="outlined")
        redact_button.bind(on_release=self.redact_message)
        redact_row.add_widget(self.redact_room_field)
        redact_row.add_widget(self.redact_event_field)
        redact_row.add_widget(redact_button)
        outer.add_widget(redact_row)

        self.status_label = MDLabel(text="", halign="center", size_hint_y=None, height=dp(30))
        outer.add_widget(self.status_label)

        logout_button = MDButton(MDButtonText(text="Log out"), style="text")
        logout_button.bind(on_release=self.logout)
        outer.add_widget(logout_button)

        self.add_widget(scroll_outer)

    def on_pre_enter(self, *args):
        self.refresh_user_list()

    def _admin_headers(self):
        app = MDApp.get_running_app()
        return {"Authorization": f"Bearer {app.client.access_token}"}

    def _to_user_id(self, username):
        app = MDApp.get_running_app()
        domain = app.client.homeserver.split("://")[-1].split(":")[0]
        return username if username.startswith("@") else f"@{username}:{domain}"

    def refresh_user_list(self):
        self.user_list_layout.clear_widgets()
        for username, info in list_users().items():
            row = BoxLayout(orientation="horizontal", size_hint_y=None, height=dp(48), spacing=dp(6))
            label_text = f"{username} {'[ADMIN]' if info['is_superuser'] else ''}"
            row.add_widget(MDLabel(text=label_text, size_hint_x=0.3))

            toggle_btn = MDButton(MDButtonText(text="Demote" if info["is_superuser"] else "Promote"), style="filled")
            toggle_btn.target_username = username
            toggle_btn.currently_admin = info["is_superuser"]
            toggle_btn.bind(on_release=self.toggle_promote)
            row.add_widget(toggle_btn)

            deactivate_btn = MDButton(MDButtonText(text="Deactivate"), style="outlined")
            deactivate_btn.target_username = username
            deactivate_btn.bind(on_release=self.deactivate_user)
            row.add_widget(deactivate_btn)

            self.user_list_layout.add_widget(row)

    def register_user(self, *args):
        username = self.new_username_field.text.strip()
        password = self.new_password_field.text
        if not username or not password:
            self.status_label.text = "Username and password required"
            return
        self.status_label.text = "Creating account..."
        asyncio.create_task(self._register_user(username, password))

    async def _register_user(self, username, password):
        app = MDApp.get_running_app()
        client = AsyncClient(app.client.homeserver, username)
        resp = await client.register(username, password, device_name="chatapp")
        if isinstance(resp, RegisterResponse):
            add_user(username, password, is_superuser=False)
            self.status_label.text = f"Created {username}"
            self.new_username_field.text = ""
            self.new_password_field.text = ""
            self.refresh_user_list()
        else:
            self.status_label.text = f"Failed: {resp}"
        await client.close()

    def toggle_promote(self, instance):
        username = instance.target_username
        new_value = not instance.currently_admin
        self.status_label.text = f"{'Promoting' if new_value else 'Demoting'} {username}..."
        asyncio.create_task(self._toggle_promote(username, new_value))

    async def _toggle_promote(self, username, new_value):
        set_superuser(username, new_value)
        app = MDApp.get_running_app()
        url = f"{app.client.homeserver}/_synapse/admin/v1/users/{self._to_user_id(username)}/admin"
        try:
            resp = requests.put(url, headers=self._admin_headers(), json={"admin": new_value}, timeout=10)
            if resp.status_code == 200:
                self.status_label.text = f"{username} {'promoted' if new_value else 'demoted'} (local + server)"
            else:
                self.status_label.text = f"{username} updated locally, server call failed: {resp.status_code}"
        except Exception as e:
            self.status_label.text = f"{username} updated locally, server call failed: {e}"
        self.refresh_user_list()

    def deactivate_user(self, instance):
        username = instance.target_username
        self.status_label.text = f"Deactivating {username}..."
        asyncio.create_task(self._deactivate_user(username))

    async def _deactivate_user(self, username):
        app = MDApp.get_running_app()
        url = f"{app.client.homeserver}/_synapse/admin/v1/deactivate/{self._to_user_id(username)}"
        try:
            resp = requests.post(url, headers=self._admin_headers(), json={"erase": False}, timeout=10)
            if resp.status_code == 200:
                self.status_label.text = f"{username} deactivated"
            else:
                self.status_label.text = f"Deactivate failed: {resp.status_code} {resp.text}"
        except Exception as e:
            self.status_label.text = f"Deactivate failed: {e}"
        self.refresh_user_list()

    def reset_password(self, *args):
        username = self.reset_username_field.text.strip()
        new_password = self.reset_password_field.text
        if not username or not new_password:
            self.status_label.text = "Username and new password required"
            return
        self.status_label.text = f"Resetting password for {username}..."
        asyncio.create_task(self._reset_password(username, new_password))

    async def _reset_password(self, username, new_password):
        app = MDApp.get_running_app()
        url = f"{app.client.homeserver}/_synapse/admin/v1/reset_password/{self._to_user_id(username)}"
        try:
            resp = requests.post(url, headers=self._admin_headers(), json={"new_password": new_password, "logout_devices": True}, timeout=10)
            if resp.status_code == 200:
                users = list_users()
                if username in users:
                    add_user(username, new_password, is_superuser=users[username]["is_superuser"])
                self.status_label.text = f"Password reset for {username}"
                self.reset_username_field.text = ""
                self.reset_password_field.text = ""
            else:
                self.status_label.text = f"Reset failed: {resp.status_code} {resp.text}"
        except Exception as e:
            self.status_label.text = f"Reset failed: {e}"

    def kick_user(self, *args):
        room_id = self.mod_room_field.text.strip()
        user_id = self._to_user_id(self.mod_user_field.text.strip())
        if not room_id or not user_id:
            self.status_label.text = "Room ID and user required"
            return
        self.status_label.text = f"Kicking {user_id}..."
        asyncio.create_task(self._room_action("kick", room_id, user_id))

    def ban_user(self, *args):
        room_id = self.mod_room_field.text.strip()
        user_id = self._to_user_id(self.mod_user_field.text.strip())
        if not room_id or not user_id:
            self.status_label.text = "Room ID and user required"
            return
        self.status_label.text = f"Banning {user_id}..."
        asyncio.create_task(self._room_action("ban", room_id, user_id))

    async def _room_action(self, action, room_id, user_id):
        app = MDApp.get_running_app()
        url = f"{app.client.homeserver}/_synapse/admin/v1/rooms/{room_id}/{action}"
        try:
            resp = requests.post(url, headers=self._admin_headers(), json={"user_id": user_id}, timeout=10)
            if resp.status_code == 200:
                self.status_label.text = f"{action.capitalize()}ned {user_id} from {room_id}"
            else:
                self.status_label.text = f"{action} failed: {resp.status_code} {resp.text}"
        except Exception as e:
            self.status_label.text = f"{action} failed: {e}"

    def redact_message(self, *args):
        room_id = self.redact_room_field.text.strip()
        event_id = self.redact_event_field.text.strip()
        if not room_id or not event_id:
            self.status_label.text = "Room ID and event ID required"
            return
        self.status_label.text = "Deleting message..."
        asyncio.create_task(self._redact_message(room_id, event_id))

    async def _redact_message(self, room_id, event_id):
        app = MDApp.get_running_app()
        resp = await app.client.room_redact(room_id, event_id, reason="Removed by admin")
        self.status_label.text = f"Redact result: {resp}"

    def logout(self, *args):
        MDApp.get_running_app().root.current = "login"


class ChatScreen(MDScreen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.name = "chat"
        self.room_id = None
        outer = BoxLayout(orientation="vertical")
        back_button = MDButton(MDButtonText(text="Back to rooms"), style="text")
        back_button.bind(on_release=self.go_back)
        self.messages_layout = BoxLayout(orientation="vertical", spacing=dp(4), padding=dp(8), size_hint_y=None)
        self.messages_layout.bind(minimum_height=self.messages_layout.setter("height"))
        self.scroll = ScrollView()
        self.scroll.add_widget(self.messages_layout)
        input_row = BoxLayout(orientation="horizontal", size_hint_y=None, height=dp(56), spacing=dp(8), padding=dp(8))
        self.message_input = MDTextField(hint_text="Message")
        self.message_input.bind(on_text_validate=self.send_message)
        send_button = MDButton(MDButtonText(text="Send"), style="filled")
        send_button.bind(on_release=self.send_message)
        input_row.add_widget(self.message_input)
        input_row.add_widget(send_button)
        outer.add_widget(back_button)
        outer.add_widget(self.scroll)
        outer.add_widget(input_row)
        self.add_widget(outer)

    def go_back(self, *args):
        MDApp.get_running_app().root.current = "rooms"

    def load_messages(self):
        asyncio.create_task(self._load_messages())

    async def _load_messages(self):
        app = MDApp.get_running_app()
        self.messages_layout.clear_widgets()
        history = await app.client.room_messages(self.room_id, start="", limit=20)
        for event in reversed(history.chunk):
            if isinstance(event, RoomMessageText):
                self.append_message(event.sender, event.body)

    def append_message(self, sender, body):
        app = MDApp.get_running_app()

        def highlight(match):
            return f"[color=42a5f5][b]{match.group(0)}[/b][/color]"

        highlighted_body = re.sub(r"@[\w.\-]+(:[\w.\-]+)?", highlight, body)

        my_username = getattr(app, "current_username", None)
        i_was_mentioned = bool(my_username) and f"@{my_username}" in body

        label = MDLabel(
            text=f"{sender}: {highlighted_body}",
            markup=True,
            size_hint_y=None,
            height=dp(30),
            font_name=app.theme.get("font_regular", "Roboto"),
            font_size=app.theme.get("font_size", 16),
        )
        if i_was_mentioned:
            glow_enabled = app.theme.get("overlay_glow", True)
            if glow_enabled:
                accent = COLOR_RGB.get(app.theme.get("primary_color", "Blue"), (0.2, 0.5, 1))
                label.md_bg_color = (accent[0], accent[1], accent[2], 0.25)
            else:
                label.md_bg_color = (0.3, 0.25, 0.05, 1)

        self.messages_layout.add_widget(label)
        self.scroll.scroll_to(label)

    def send_message(self, *args):
        text = self.message_input.text
        if not text:
            return
        asyncio.create_task(self._send_message(text))
        self.message_input.text = ""

    async def _send_message(self, text):
        app = MDApp.get_running_app()
        await app.client.room_send(
            room_id=self.room_id,
            message_type="m.room.message",
            content={"msgtype": "m.text", "body": text},
        )


class ChatApp(MDApp):
    client = None
    theme = None
    sync_task = None
    current_username = None

    def build(self):
        self.theme = load_theme()
        self.theme_cls.theme_style = self.theme.get("theme_style", "Dark")
        self.theme_cls.primary_palette = self.theme.get("primary_color", "Blue")

        if self.theme.get("use_gradient", False):
            from kivy.core.window import Window
            accent = COLOR_RGB.get(self.theme.get("primary_color", "Blue"), (0.2, 0.5, 1))
            top_color = (accent[0] * 0.25, accent[1] * 0.25, accent[2] * 0.35, 1)
            bottom_color = (0.05, 0.05, 0.08, 1)
            gradient = GradientBackground(top_color=top_color, bottom_color=bottom_color)
            gradient.size_hint = (1, 1)
            Window.bind(size=lambda *a: setattr(gradient, "size", Window.size))
            gradient.size = Window.size

        font_regular_path = os.path.join(os.path.dirname(__file__), "fonts", f'{self.theme.get("font_regular", "Roboto")}.ttf')
        if os.path.exists(font_regular_path):
            LabelBase.register(name=self.theme["font_regular"], fn_regular=font_regular_path)
        sm = MDScreenManager()
        sm.add_widget(LoginScreen())
        sm.add_widget(RegisterScreen())
        sm.add_widget(NewChatScreen())
        sm.add_widget(NewGroupScreen())
        sm.add_widget(RoomListScreen())
        sm.add_widget(ChatScreen())
        sm.add_widget(ThemeSettingsScreen())
        sm.add_widget(AdminScreen())
        return sm

    def start_sync_loop(self):
        if self.sync_task is None:
            self.client.add_event_callback(self.on_message, RoomMessageText)
            self.client.add_response_callback(self.on_sync, SyncResponse)
            self.sync_task = asyncio.create_task(self.client.sync_forever(timeout=30000))

    async def on_message(self, room, event):
        chat_screen = self.root.get_screen("chat")
        if chat_screen.room_id == room.room_id:
            chat_screen.append_message(event.sender, event.body)
        self.root.get_screen("rooms").refresh_room_buttons()

    async def on_sync(self, response):
        for room_id in list(self.client.invited_rooms.keys()):
            await self.client.join(room_id)
        self.root.get_screen("rooms").refresh_room_buttons()


if __name__ == "__main__":
    asyncio.run(ChatApp().async_run(async_lib="asyncio"))
