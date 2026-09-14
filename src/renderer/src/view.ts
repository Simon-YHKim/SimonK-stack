import { VIEW_IDS, type ViewId } from '../../shared/types';

export function parseViewFromSearch(search: string): ViewId {
  const view = new URLSearchParams(search).get('view');
  return VIEW_IDS.find((id) => id === view) ?? 'widget';
}
