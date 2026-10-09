// talos-player: plays one audio file and registers as macOS "Now Playing", so the keyboard
// media keys control Talos like any music app: ⏯ pause/resume, ⏭ skip, and it shows in Control Center.
// Usage: talos-player <file> [title]
import AVFoundation
import AppKit
import MediaPlayer

guard CommandLine.arguments.count > 1 else {
    FileHandle.standardError.write("usage: talos-player <file> [title]\n".data(using: .utf8)!)
    exit(2)
}
let url = URL(fileURLWithPath: CommandLine.arguments[1])
let title = CommandLine.arguments.count > 2 ? CommandLine.arguments[2] : "Talos"

final class Player: NSObject, AVAudioPlayerDelegate {
    let audio: AVAudioPlayer
    init(url: URL) throws {
        audio = try AVAudioPlayer(contentsOf: url)
        super.init()
        audio.delegate = self
    }
    func audioPlayerDidFinishPlaying(_ player: AVAudioPlayer, successfully flag: Bool) { finish() }
    func finish() {
        MPNowPlayingInfoCenter.default().playbackState = .stopped
        MPNowPlayingInfoCenter.default().nowPlayingInfo = nil
        exit(0)
    }
    func updateInfo() {
        MPNowPlayingInfoCenter.default().nowPlayingInfo = [
            MPMediaItemPropertyTitle: title,
            MPMediaItemPropertyArtist: "Talos",
            MPMediaItemPropertyPlaybackDuration: audio.duration,
            MPNowPlayingInfoPropertyElapsedPlaybackTime: audio.currentTime,
            MPNowPlayingInfoPropertyPlaybackRate: audio.isPlaying ? 1.0 : 0.0,
        ]
        MPNowPlayingInfoCenter.default().playbackState = audio.isPlaying ? .playing : .paused
    }
}

let app = NSApplication.shared
app.setActivationPolicy(.prohibited)  // no Dock icon
let player: Player
do { player = try Player(url: url) } catch {
    FileHandle.standardError.write("cannot open \(url.path): \(error)\n".data(using: .utf8)!)
    exit(1)
}
let cc = MPRemoteCommandCenter.shared()
cc.togglePlayPauseCommand.addTarget { _ in
    if player.audio.isPlaying { player.audio.pause() } else { player.audio.play() }
    player.updateInfo(); return .success
}
cc.pauseCommand.addTarget { _ in player.audio.pause(); player.updateInfo(); return .success }
cc.playCommand.addTarget { _ in player.audio.play(); player.updateInfo(); return .success }
cc.stopCommand.addTarget { _ in player.audio.stop(); player.finish(); return .success }
cc.nextTrackCommand.addTarget { _ in player.audio.stop(); player.finish(); return .success }
signal(SIGTERM) { _ in
    MPNowPlayingInfoCenter.default().nowPlayingInfo = nil
    exit(0)
}

player.audio.prepareToPlay()
player.audio.play()
player.updateInfo()
app.run()
