"""Player control implementation (org.mpris.MediaPlayer2.Player)."""
import logging
from typing import TYPE_CHECKING, Dict

from dbus_next.service import (
    PropertyAccess,
    ServiceInterface,
    Variant,
    dbus_property,
    method,
    signal,
)

if TYPE_CHECKING:
    from .hassinterface import HassInterface


_LOGGER = logging.getLogger(__name__)


class PlayerInterface(ServiceInterface):
    """Implementation of org.mpris.MediaPlayer2.Player dbus interface.

    Controls homeassistant over its websocket API.
    """

    def __init__(self, name, hass_interface: "HassInterface"):
        _LOGGER.debug("Initializing %s", name)
        super().__init__(name)
        self.data: Dict = {}
        self.hass_interface = hass_interface
        self.entity = None

    def update_data(self, data):
        """Update the internal data structure and emit PropertiesChanged for MPRIS listeners."""
        self.data = data
        # flatten data
        self.entity = self.data["entity_id"]
        self.data.update(self.data["attributes"])
        _LOGGER.debug("Updating %s, emiting properties changed.", self.entity)
        changed_attrs = {
            "Metadata": self.Metadata,
            "Position": self.Position,
            "PlaybackStatus": self.PlaybackStatus,
            "Rate": self.Rate,
        }
        self.emit_properties_changed(changed_attrs)

    @method()
    async def Next(self):
        """Next track."""
        await self.hass_interface.execute_media_player_command(
            "media_next_track", self.entity
        )

    @method()
    async def Previous(self):
        """Previous track."""
        await self.hass_interface.execute_media_player_command(
            "media_previous_track", self.entity
        )

    @method()
    async def Pause(self):
        """Pause."""
        await self.hass_interface.execute_media_player_command(
            "media_pause", self.entity
        )

    @method()
    async def PlayPause(self):
        """Play/pause."""
        await self.hass_interface.execute_media_player_command(
            "media_play_pause", self.entity
        )

    @method()
    async def Stop(self):
        """Stop playing."""
        await self.hass_interface.execute_media_player_command(
            "media_stop", self.entity
        )

    @method()
    async def Play(self):
        """Play."""
        await self.hass_interface.execute_media_player_command(
            "media_play", self.entity
        )

    # Seek (x: Offset) → nothing
    # Parameters
    # Offset — x (Time_In_Us)
    # The number of microseconds to seek forward.
    #
    # Seeks forward in the current track by the specified number of microseconds.
    #
    # A negative value seeks back. If this would mean seeking back further than the start of the track, the position is set to 0.
    #
    # If the value passed in would mean seeking beyond the end of the track, acts like a call to Next.
    @method()
    async def Seek(self, seek_in_us: "x"):  # type: ignore
        """Seek +- given `seek_in_us`."""
        seek_to = (self.Metadata + seek_in_us) / 1_000_000
        self.hass_interface.schedule_seek(seek_to, self.entity)

    # SetPosition (o: TrackId, x: Position) → nothing
    # Parameters
    # TrackId — o (Track_Id)
    # The currently playing track's identifier.
    #
    # If this does not match the id of the currently-playing track, the call is ignored as "stale".
    # /org/mpris/MediaPlayer2/TrackList/NoTrack is not a valid value for this argument.
    #
    # Position — x (Time_In_Us)
    # Track position in microseconds.
    # This must be between 0 and <track_length>.
    @method()
    async def SetPosition(self, trackid: "o", seek_to: "x"):  # type: ignore
        """Seek to specific position in the current track."""
        self.hass_interface.schedule_seek(seek_to / 1_000_000, self.entity)

    # OpenUri (s: Uri) → nothing
    # Parameters
    # Uri — s (Uri)
    # Uri of the track to load. Its uri scheme should be an element of the org.mpris.MediaPlayer2.SupportedUriSchemes property and the mime-type should match one of the elements of the org.mpris.MediaPlayer2.SupportedMimeTypes.
    #
    # Opens the Uri given as an argument
    #
    # If the playback is stopped, starts playing
    @method()
    async def OpenUri(self):
        """Play given URL on the media player."""
        raise NotImplementedError()

    # Seeked (x: Position)
    # Parameters
    # Position — x (Time_In_Us)
    # The new position, in microseconds.
    #
    # Indicates that the track position has changed in a way that is inconsistant with the current playing state.
    #
    # When this signal is not received, clients should assume that:
    #
    # When playing, the position progresses according to the rate property.
    # When paused, it remains constant.
    @signal()
    async def Seeked(self):
        """Signal players that the position has changed."""
        raise NotImplementedError()

    @dbus_property(access=PropertyAccess.READ)
    def PlaybackStatus(self) -> "s":  # type: ignore
        """Return the current playback status.

        May be "Playing", "Paused" or "Stopped".
        """
        return self.data.get("state", "").capitalize()

    # LoopStatus — s (Loop_Status)
    # Read/Write
    # This property is optional. Clients should handle its absence gracefully.
    # This property is optional. Clients should handle its absence gracefully.

    # Rate — d (Playback_Rate)
    # Read/Write
    # When this property changes, the org.freedesktop.DBus.Properties.PropertiesChanged signal is emitted with the new value.
    # The current playback rate.
    # TODO: implement write?
    @dbus_property(access=PropertyAccess.READ)
    def Rate(self) -> "d":  # type: ignore
        """Return playback rate. This is static 1.0 for us."""
        return 1.0

    # Shuffle — b
    # Read/Write
    # This property is optional. Clients should handle its absence gracefully.
    # TODO: implement write?
    @dbus_property(access=PropertyAccess.READ)
    def Shuffle(self) -> "b":  # type: ignore
        """Return True if shuffle is enabled."""
        return self.data.get("shuffle", False)

    # Metadata — a{sv} (Metadata_Map)
    # Read only
    # When this property changes, the org.freedesktop.DBus.Properties.PropertiesChanged signal is emitted with the new value.
    # The metadata of the current element.
    @dbus_property(access=PropertyAccess.READ)
    def Metadata(self) -> "a{sv}":  # type: ignore
        """Return the metadata used by MPRIS players to display what is being played."""
        cover_url = f'{self.hass_interface.http_endpoint}{self.data.get("entity_picture", None)}'
        duration = self.data.get("media_duration", 0)
        duration = int(duration) * 1_000_000

        return {
            # we do not support playlists, so we don't care about track ids.
            "mpris:trackid": Variant("o", "/fi/iki/tpr/hassbridge/trackiddummy"),
            "mpris:artUrl": Variant("s", cover_url),
            "mpris:length": Variant("x", duration),
            "xesam:artist": Variant(
                "s", self.data.get("media_artist", "<unavailable artist>")
            ),
            "xesam:album": Variant(
                "s", self.data.get("media_album_name", "<unavailable album>")
            ),
            "xesam:title": Variant(
                "s", self.data.get("media_title", "<unavailable title>")
            ),
        }

    # Volume — d (Volume)
    # Read/Write
    # When this property changes, the org.freedesktop.DBus.Properties.PropertiesChanged signal is emitted with the new value.
    # The volume level.
    @dbus_property(access=PropertyAccess.READWRITE)
    def Volume(self) -> "d":  # type: ignore
        """Return current volume level."""
        vol = self.data.get("volume_level", 0)
        return vol

    @Volume.setter
    def VolumeSetter(self, vol: "d"):  # type: ignore
        """Set volume."""
        self.hass_interface.schedule_set_volume(vol, self.entity)

    # Position — x (Time_In_Us)
    # Read only
    # The org.freedesktop.DBus.Properties.PropertiesChanged signal is not emitted when this property changes.
    # The current track position in microseconds, between 0 and the 'mpris:length' metadata entry (see Metadata).
    @dbus_property(access=PropertyAccess.READ)
    def Position(self) -> "x":  # type: ignore
        """Return current media position."""
        return int(self.data.get("media_position", 0)) * 1_000_000

    # MinimumRate — d (Playback_Rate)
    # Read only
    # When this property changes, the org.freedesktop.DBus.Properties.PropertiesChanged signal is emitted with the new value.
    @dbus_property(access=PropertyAccess.READ)
    def MinimumRate(self) -> "d":  # type: ignore
        """Return minimum playback rate. This is static 1.0 for us."""
        return 1.0

    # MaximumRate — d (Playback_Rate)
    # Read only
    # When this property changes, the org.freedesktop.DBus.Properties.PropertiesChanged signal is emitted with the new value.
    @dbus_property(access=PropertyAccess.READ)
    def MaximumRate(self) -> "d":  # type: ignore
        """Return maximum playback rate. This is static 1.0 for us."""
        return 1.0

    # CanGoNext — b
    # Read only
    # When this property changes, the org.freedesktop.DBus.Properties.PropertiesChanged signal is emitted with the new value.
    @dbus_property(access=PropertyAccess.READ)
    def CanGoNext(self) -> "b":  # type: ignore
        """We support playback controls."""
        return True

    # CanGoPrevious — b
    # Read only
    # When this property changes, the org.freedesktop.DBus.Properties.PropertiesChanged signal is emitted with the new value.
    @dbus_property(access=PropertyAccess.READ)
    def CanGoPrevious(self) -> "b":  # type: ignore
        """We support playback controls."""
        return True

    # CanPlay — b
    # Read only
    # When this property changes, the org.freedesktop.DBus.Properties.PropertiesChanged signal is emitted with the new value.
    # Whether playback can be started using Play or PlayPause.
    @dbus_property(access=PropertyAccess.READ)
    def CanPlay(self) -> "b":  # type: ignore
        """We support playback controls."""
        return True

    # CanPause — b
    # Read only
    # When this property changes, the org.freedesktop.DBus.Properties.PropertiesChanged signal is emitted with the new value.
    # Whether playback can be paused using Pause or PlayPause.
    @dbus_property(access=PropertyAccess.READ)
    def CanPause(self) -> "b":  # type: ignore
        """We support playback controls."""
        return True

    # CanSeek — b
    # Read only
    # When this property changes, the org.freedesktop.DBus.Properties.PropertiesChanged signal is emitted with the new value.
    # Whether the client can control the playback position using Seek and SetPosition. This may be different for different tracks.
    @dbus_property(access=PropertyAccess.READ)
    def CanSeek(self) -> "b":  # type: ignore
        """We support playback controls."""
        return True

    # CanControl — b
    # Read only
    # The org.freedesktop.DBus.Properties.PropertiesChanged signal is not emitted when this property changes.
    # Whether the media player may be controlled over this interface.
    @dbus_property(access=PropertyAccess.READ)
    def CanControl(self) -> "b":  # type: ignore
        """We support playback controls."""
        return True
