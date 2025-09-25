const axios = require('axios');

class APIClient {
  constructor(baseURL = 'https://pifa-friends.preview.emergentagent.com/api') {
    this.baseURL = baseURL;
    this.defaultHeaders = {
      'Content-Type': 'application/json'
    };
  }

  setAuthToken(token) {
    if (token) {
      this.defaultHeaders['Authorization'] = `Bearer ${token}`;
    } else {
      delete this.defaultHeaders['Authorization'];
    }
  }

  async request(method, endpoint, data = null, customHeaders = {}) {
    const url = `${this.baseURL}${endpoint}`;
    const headers = { ...this.defaultHeaders, ...customHeaders };
    
    try {
      const response = await axios({
        method,
        url,
        data,
        headers,
        timeout: 15000
      });
      return { success: true, data: response.data, status: response.status };
    } catch (error) {
      return {
        success: false,
        error: error.response?.data || error.message,
        status: error.response?.status || 0
      };
    }
  }

  // Auth methods
  async requestMagicLink(email) {
    return this.request('POST', '/auth/request-magic-link', { email });
  }

  async verifyMagicLink(token) {
    return this.request('POST', '/auth/verify-magic-link', { token });
  }

  // League methods
  async createLeague(leagueData) {
    return this.request('POST', '/leagues', leagueData);
  }

  async getLeague(leagueId) {
    return this.request('GET', `/leagues/${leagueId}`);
  }

  async updateLeagueSettings(leagueId, settings) {
    return this.request('PATCH', `/leagues/${leagueId}/settings`, settings);
  }

  // Member methods
  async inviteMembers(leagueId, emails) {
    return this.request('POST', `/leagues/${leagueId}/invite`, { emails });
  }

  async acceptInvitation(invitationId) {
    return this.request('POST', `/invitations/${invitationId}/accept`);
  }

  async getLeagueMembers(leagueId) {
    return this.request('GET', `/leagues/${leagueId}/members`);
  }

  // Auction methods
  async startAuction(leagueId) {
    return this.request('POST', `/admin/leagues/${leagueId}/auction/start`);
  }

  async pauseAuction(leagueId) {
    return this.request('POST', `/admin/leagues/${leagueId}/auction/pause`);
  }

  async resumeAuction(leagueId) {
    return this.request('POST', `/admin/leagues/${leagueId}/auction/resume`);
  }

  async getAuction(leagueId) {
    return this.request('GET', `/auctions/${leagueId}`);
  }

  async getCurrentLot(auctionId) {
    return this.request('GET', `/auctions/${auctionId}/current-lot`);
  }

  async placeBid(lotId, amount) {
    return this.request('POST', `/lots/${lotId}/bid`, { amount });
  }

  // Data methods
  async getMyClubs(leagueId) {
    return this.request('GET', `/clubs/my-clubs/${leagueId}`);
  }

  async getFixtures(leagueId) {
    return this.request('GET', `/leagues/${leagueId}/fixtures`);
  }

  async getLeaderboard(leagueId) {
    return this.request('GET', `/leagues/${leagueId}/leaderboard`);
  }

  // Scoring methods
  async ingestResult(resultData) {
    return this.request('POST', '/ingest/final_result', resultData);
  }

  // Test cleanup methods
  async deleteUser(userId) {
    return this.request('DELETE', `/users/${userId}`);
  }

  async deleteLeague(leagueId) {
    return this.request('DELETE', `/leagues/${leagueId}`);
  }

  // Competition profiles
  async getCompetitionProfiles() {
    return this.request('GET', '/competition-profiles');
  }
}

module.exports = APIClient;