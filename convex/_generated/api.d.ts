/* eslint-disable */
/**
 * Generated `api` utility.
 *
 * THIS CODE IS AUTOMATICALLY GENERATED.
 *
 * To regenerate, run `npx convex dev`.
 * @module
 */

import type {
  ApiFromModules,
  FilterApi,
  FunctionReference,
} from "convex/server";
import type * as agent_conversation from "../agent/conversation.js";
import type * as agent_embeddingsCache from "../agent/embeddingsCache.js";
import type * as agent_memory from "../agent/memory.js";
import type * as wetwijzer_agent from "../wetwijzer/agent.js";
import type * as wetwijzer_agentDescription from "../wetwijzer/agentDescription.js";
import type * as wetwijzer_agentInputs from "../wetwijzer/agentInputs.js";
import type * as wetwijzer_agentOperations from "../wetwijzer/agentOperations.js";
import type * as wetwijzer_clientAgentOperations from "../wetwijzer/clientAgentOperations.js";
import type * as wetwijzer_conversation from "../wetwijzer/conversation.js";
import type * as wetwijzer_conversationMembership from "../wetwijzer/conversationMembership.js";
import type * as wetwijzer_game from "../wetwijzer/game.js";
import type * as wetwijzer_ids from "../wetwijzer/ids.js";
import type * as wetwijzer_inputHandler from "../wetwijzer/inputHandler.js";
import type * as wetwijzer_inputs from "../wetwijzer/inputs.js";
import type * as wetwijzer_insertInput from "../wetwijzer/insertInput.js";
import type * as wetwijzer_location from "../wetwijzer/location.js";
import type * as wetwijzer_main from "../wetwijzer/main.js";
import type * as wetwijzer_movement from "../wetwijzer/movement.js";
import type * as wetwijzer_player from "../wetwijzer/player.js";
import type * as wetwijzer_playerDescription from "../wetwijzer/playerDescription.js";
import type * as wetwijzer_world from "../wetwijzer/world.js";
import type * as wetwijzer_worldMap from "../wetwijzer/worldMap.js";
import type * as clientLLMRequests from "../clientLLMRequests.js";
import type * as constants from "../constants.js";
import type * as crons from "../crons.js";
import type * as engine_abstractGame from "../engine/abstractGame.js";
import type * as engine_historicalObject from "../engine/historicalObject.js";
import type * as http from "../http.js";
import type * as init from "../init.js";
import type * as messages from "../messages.js";
import type * as music from "../music.js";
import type * as testing from "../testing.js";
import type * as util_FastIntegerCompression from "../util/FastIntegerCompression.js";
import type * as util_assertNever from "../util/assertNever.js";
import type * as util_asyncMap from "../util/asyncMap.js";
import type * as util_compression from "../util/compression.js";
import type * as util_geometry from "../util/geometry.js";
import type * as util_isSimpleObject from "../util/isSimpleObject.js";
import type * as util_llm from "../util/llm.js";
import type * as util_minheap from "../util/minheap.js";
import type * as util_object from "../util/object.js";
import type * as util_sleep from "../util/sleep.js";
import type * as util_types from "../util/types.js";
import type * as util_xxhash from "../util/xxhash.js";
import type * as world from "../world.js";

/**
 * A utility for referencing Convex functions in your app's API.
 *
 * Usage:
 * ```js
 * const myFunctionReference = api.myModule.myFunction;
 * ```
 */
declare const fullApi: ApiFromModules<{
  "agent/conversation": typeof agent_conversation;
  "agent/embeddingsCache": typeof agent_embeddingsCache;
  "agent/memory": typeof agent_memory;
  "wetwijzer/agent": typeof wetwijzer_agent;
  "wetwijzer/agentDescription": typeof wetwijzer_agentDescription;
  "wetwijzer/agentInputs": typeof wetwijzer_agentInputs;
  "wetwijzer/agentOperations": typeof wetwijzer_agentOperations;
  "wetwijzer/clientAgentOperations": typeof wetwijzer_clientAgentOperations;
  "wetwijzer/conversation": typeof wetwijzer_conversation;
  "wetwijzer/conversationMembership": typeof wetwijzer_conversationMembership;
  "wetwijzer/game": typeof wetwijzer_game;
  "wetwijzer/ids": typeof wetwijzer_ids;
  "wetwijzer/inputHandler": typeof wetwijzer_inputHandler;
  "wetwijzer/inputs": typeof wetwijzer_inputs;
  "wetwijzer/insertInput": typeof wetwijzer_insertInput;
  "wetwijzer/location": typeof wetwijzer_location;
  "wetwijzer/main": typeof wetwijzer_main;
  "wetwijzer/movement": typeof wetwijzer_movement;
  "wetwijzer/player": typeof wetwijzer_player;
  "wetwijzer/playerDescription": typeof wetwijzer_playerDescription;
  "wetwijzer/world": typeof wetwijzer_world;
  "wetwijzer/worldMap": typeof wetwijzer_worldMap;
  clientLLMRequests: typeof clientLLMRequests;
  constants: typeof constants;
  crons: typeof crons;
  "engine/abstractGame": typeof engine_abstractGame;
  "engine/historicalObject": typeof engine_historicalObject;
  http: typeof http;
  init: typeof init;
  messages: typeof messages;
  music: typeof music;
  testing: typeof testing;
  "util/FastIntegerCompression": typeof util_FastIntegerCompression;
  "util/assertNever": typeof util_assertNever;
  "util/asyncMap": typeof util_asyncMap;
  "util/compression": typeof util_compression;
  "util/geometry": typeof util_geometry;
  "util/isSimpleObject": typeof util_isSimpleObject;
  "util/llm": typeof util_llm;
  "util/minheap": typeof util_minheap;
  "util/object": typeof util_object;
  "util/sleep": typeof util_sleep;
  "util/types": typeof util_types;
  "util/xxhash": typeof util_xxhash;
  world: typeof world;
}>;
export declare const api: FilterApi<
  typeof fullApi,
  FunctionReference<any, "public">
>;
export declare const internal: FilterApi<
  typeof fullApi,
  FunctionReference<any, "internal">
>;
