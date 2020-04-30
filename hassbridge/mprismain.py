"""Implementation of org.mpris.MediaPlayer2."""
import logging

from dbus_next.service import PropertyAccess, ServiceInterface, dbus_property, method

_LOGGER = logging.getLogger(__name__)


class MPrisInterface(ServiceInterface):
    """This class is responsible for the main org.mpris.MediaPlayer2 interface."""

    def __init__(self, name, hass_interface=None):
        _LOGGER.debug("Initializing dbus interface %s", name)
        super().__init__(name)
        self.hass_interface = hass_interface

    @method()
    def Quit(self):
        """Quit is not applicable."""

    @method()
    def Raise(self):
        """Raise is not applicable."""

    # Identity — s
    # Read only
    # When this property changes, the org.freedesktop.DBus.Properties.PropertiesChanged signal is emitted with the new value.
    # A friendly name to identify the media player to users.
    # This should usually match the name found in .desktop files
    # (eg: "VLC media player").
    @dbus_property(access=PropertyAccess.READ)
    def Identity(self) -> "s":  # type: ignore
        """Return our identity."""
        # TODO get friendly_name from self.hass_interface
        return "Home-assistant bridge"

    # SupportedUriSchemes — as
    # Read only
    # When this property changes, the org.freedesktop.DBus.Properties.PropertiesChanged signal is emitted with the new value.
    # The URI schemes supported by the media player.
    # This can be viewed as protocols supported by the player in almost all cases.
    # Almost every media player will include support for the "file" scheme. Other common schemes are "http" and "rtsp".
    # Note that URI schemes should be lower-case.
    @dbus_property(access=PropertyAccess.READ)
    def SupportedUriSchemes(self) -> "as":  # type: ignore
        """Just a placeholder."""
        return []

    # SupportedMimeTypes — as
    # Read only
    # When this property changes, the org.freedesktop.DBus.Properties.PropertiesChanged signal is emitted with the new value.
    # The mime-types supported by the media player.
    #
    # Mime-types should be in the standard format (eg: audio/mpeg or application/ogg).
    @dbus_property(access=PropertyAccess.READ)
    def SupportedMimeTypes(self) -> "as":  # type: ignore
        """Just a placeholder."""
        return []

    # CanRaise — b
    # Read only
    # When this property changes, the org.freedesktop.DBus.Properties.PropertiesChanged signal is emitted with the new value.
    # If false, calling Raise will have no effect, and may raise a NotSupported error.
    @dbus_property(access=PropertyAccess.READ)
    def CanRaise(self) -> "b":  # type: ignore
        """Raise is not applicable."""
        return False

    # CanQuit — b
    # Read only
    # When this property changes, the org.freedesktop.DBus.Properties.PropertiesChanged signal is emitted with the new value.
    # If false, calling Quit will have no effect, and may raise a NotSupported error.
    @dbus_property(access=PropertyAccess.READ)
    def CanQuit(self) -> "b":  # type: ignore
        """Quit is not applicable."""
        return False

    # Fullscreen — b
    # Read/Write
    # Added in 2.2.
    # This property is optional. Clients should handle its absence gracefully.

    # CanSetFullscreen — b
    # Read only
    # Added in 2.2.
    # This property is optional. Clients should handle its absence gracefully.

    # HasTrackList — b
    # Read only
    # When this property changes, the org.freedesktop.DBus.Properties.PropertiesChanged signal is emitted with the new value.
    # Indicates whether the /org/mpris/MediaPlayer2 object implements the org.mpris.MediaPlayer2.TrackList interface.
    @dbus_property(access=PropertyAccess.READ)
    def HasTrackList(self) -> "b":  # type: ignore
        """Playlist interface is not implemented."""
        return False
