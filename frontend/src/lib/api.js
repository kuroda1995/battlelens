const API_BASE = window.__API_BASE__ || 'http://localhost:8000';

async function request(path, options = {}) {
	const res = await fetch(`${API_BASE}${path}`, {
		headers: { 'Content-Type': 'application/json' },
		...options
	});
	if (!res.ok) {
		let detail = res.statusText;
		try {
			const body = await res.json();
			detail = body.detail ?? JSON.stringify(body);
		} catch {
			// レスポンスボディがJSONでない場合はstatusTextのままにする
		}
		throw new Error(`APIエラー (${res.status}): ${detail}`);
	}
	if (res.status === 204) return null;
	return res.json();
}

export function searchSpecies(query) {
	const params = new URLSearchParams({ q: query ?? '' });
	return request(`/species/search?${params}`);
}

export function getSpeciesDetail(idOrName) {
	return request(`/species/${idOrName}`);
}

export function listParties() {
	return request('/parties');
}

export function getParty(id) {
	return request(`/parties/${id}`);
}

export function createParty(payload) {
	return request('/parties', { method: 'POST', body: JSON.stringify(payload) });
}

export function updateParty(id, payload) {
	return request(`/parties/${id}`, { method: 'PUT', body: JSON.stringify(payload) });
}

export function deleteParty(id) {
	return request(`/parties/${id}`, { method: 'DELETE' });
}

export function calcStats(payload) {
	return request('/calc/stats', { method: 'POST', body: JSON.stringify(payload) });
}
