// @ts-nocheck
import * as __fd_glob_4 from "../content/docs/options-reference.mdx?collection=docs"
import * as __fd_glob_3 from "../content/docs/npx-daemon.mdx?collection=docs"
import * as __fd_glob_2 from "../content/docs/index.mdx?collection=docs"
import * as __fd_glob_1 from "../content/docs/getting-started.mdx?collection=docs"
import * as __fd_glob_0 from "../content/docs/api.mdx?collection=docs"
import { server } from 'fumadocs-mdx/runtime/server';
import type * as Config from '../source.config';

const create = server<typeof Config, import("fumadocs-mdx/runtime/types").InternalTypeConfig & {
  DocData: {
  }
}>({"doc":{"passthroughs":["extractedReferences"]}});

export const docs = await create.doc("docs", "content/docs", {"api.mdx": __fd_glob_0, "getting-started.mdx": __fd_glob_1, "index.mdx": __fd_glob_2, "npx-daemon.mdx": __fd_glob_3, "options-reference.mdx": __fd_glob_4, });

export const meta = await create.meta("meta", "content/docs", {});