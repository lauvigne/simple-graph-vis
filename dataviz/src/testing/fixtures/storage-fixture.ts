import { StorageData } from '../../app/models/storage-data';

export const storageFixture: StorageData = {
  version: '2.0',
  format: 'compact-graph',
  sources: [{ name: 'fixture.xlsx', sheets: [{ name: 'Capabilities', rowCount: 4 }] }],
  warnings: [],
  graph: {
    nodes: [
      { k: 'entity:E1', i: 'E1', t: 'entity', l: 'E1' },
      { k: 'application:wide', i: 'wide', t: 'application', l: 'Wide App', m: { entity: 'E1', applicationCode: 'APP-WIDE' } },
      { k: 'application:narrow', i: 'narrow', t: 'application', l: 'Narrow App', m: { entity: 'E1', applicationCode: 'APP-NARROW' } },
      { k: 'application:partial', i: 'partial', t: 'application', l: 'Partial App', m: { entity: 'E1', applicationCode: 'APP-PARTIAL' } },
      { k: 'application:other', i: 'other', t: 'application', l: 'Other Entity App', m: { entity: 'E2', applicationCode: 'APP-OTHER' } },
      { k: 'entity:E2', i: 'E2', t: 'entity', l: 'E2' },
      { k: 'businessCapacity:l1', i: 'l1', t: 'businessCapacity', l: 'L1', m: { code: '1' } },
      { k: 'businessCapacity:l2', i: 'l2', t: 'businessCapacity', l: 'L2', m: { code: '1.1' } },
      { k: 'businessCapacity:l3a', i: 'l3a', t: 'businessCapacity', l: 'L3 A', m: { code: '1.1.1' } },
      { k: 'businessCapacity:l3b', i: 'l3b', t: 'businessCapacity', l: 'L3 B', m: { code: '1.1.2' } },
      { k: 'businessCapacity:l3c', i: 'l3c', t: 'businessCapacity', l: 'L3 C', m: { code: '1.1.3' } },
    ],
    edges: [
      { s: 'businessCapacity:l1', t: 'businessCapacity:l2', r: 'contains' },
      { s: 'businessCapacity:l2', t: 'businessCapacity:l3a', r: 'contains' },
      { s: 'businessCapacity:l2', t: 'businessCapacity:l3b', r: 'contains' },
      { s: 'businessCapacity:l2', t: 'businessCapacity:l3c', r: 'contains' },
      { s: 'application:wide', t: 'entity:E1', r: 'belongs_to' },
      { s: 'application:narrow', t: 'entity:E1', r: 'belongs_to' },
      { s: 'application:partial', t: 'entity:E1', r: 'belongs_to' },
      { s: 'application:other', t: 'entity:E2', r: 'belongs_to' },
      { s: 'application:wide', t: 'businessCapacity:l2', r: 'mapped_to' },
      { s: 'application:narrow', t: 'businessCapacity:l3a', r: 'mapped_to' },
      { s: 'application:partial', t: 'businessCapacity:l3a', r: 'mapped_to' },
      { s: 'application:partial', t: 'businessCapacity:l3b', r: 'mapped_to' },
      { s: 'application:other', t: 'businessCapacity:l2', r: 'mapped_to' },
    ],
  },
};
