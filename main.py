import sys
from kivy.app import App
from kivy.utils import platform

class UltronLoader(App):
    def build(self):
        if platform == 'android':
            from jnius import autoclass
            from android.permissions import request_permissions, Permission

            request_permissions([
                Permission.RECORD_AUDIO,
                Permission.MODIFY_AUDIO_SETTINGS,
                Permission.CAMERA,
                Permission.WRITE_EXTERNAL_STORAGE,
                Permission.READ_EXTERNAL_STORAGE,
                Permission.CALL_PHONE,
                Permission.READ_PHONE_STATE
            ])

            # Matches package.domain (org.ultron.ai) + service name (ultroncore)
            service = autoclass('org.ultron.ai.ServiceUltroncore')
            mActivity = autoclass('org.kivy.android.PythonActivity').mActivity
            service.start(mActivity, '')

        # Close visible activity immediately so Ultron runs headless in background
        sys.exit(0)

if __name__ == '__main__':
    UltronLoader().run()
