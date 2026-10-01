import { Composition } from "remotion";
import { Promo, DURATION, FPS } from "./Promo";
import { Reel, REEL_DURATION } from "./Reel";
import { Journey, JOURNEY_DURATION } from "./Journey";
import { Hook, HOOK_DURATION } from "./Hook";

// One video, two shapes: 9:16 for Reels/TikTok/Shorts, 16:9 for YouTube/X.
export const Root = () => <>
  <Composition id="FigVertical" component={Promo} durationInFrames={DURATION} fps={FPS} width={1080} height={1920} />
  <Composition id="FigWide" component={Promo} durationInFrames={DURATION} fps={FPS} width={1920} height={1080} />
  <Composition id="FigReelWide" component={Reel} durationInFrames={REEL_DURATION} fps={FPS} width={1920} height={1080} />
  <Composition id="FigReelVertical" component={Reel} durationInFrames={REEL_DURATION} fps={FPS} width={1080} height={1920} />
  <Composition id="FigReelSoundWide" component={Reel} defaultProps={{ sound: true }} durationInFrames={REEL_DURATION} fps={FPS} width={1920} height={1080} />
  <Composition id="FigReelSoundVertical" component={Reel} defaultProps={{ sound: true }} durationInFrames={REEL_DURATION} fps={FPS} width={1080} height={1920} />
  <Composition id="FigJourneyWide" component={Journey} defaultProps={{ sound: true }} durationInFrames={JOURNEY_DURATION} fps={FPS} width={1920} height={1080} />
  <Composition id="FigJourneyVertical" component={Journey} defaultProps={{ sound: true }} durationInFrames={JOURNEY_DURATION} fps={FPS} width={1080} height={1920} />
  <Composition id="FigHookVertical" component={Hook} durationInFrames={HOOK_DURATION} fps={FPS} width={1080} height={1920} />
  <Composition id="FigHookWide" component={Hook} durationInFrames={HOOK_DURATION} fps={FPS} width={1920} height={1080} />
</>;
