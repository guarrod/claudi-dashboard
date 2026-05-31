import { createSlice } from '@reduxjs/toolkit';

const initialState = {
  activeSprint: null,
  sprints: [],
  isLoading: false,
  error: null,
};

const sprintSlice = createSlice({
  name: 'sprint',
  initialState,
  reducers: {
    setActiveSprint: (state, action) => {
      state.activeSprint = action.payload;
    },
    setSprints: (state, action) => {
      state.sprints = action.payload;
    },
    setLoading: (state, action) => {
      state.isLoading = action.payload;
    },
    setError: (state, action) => {
      state.error = action.payload;
    },
  },
});

export const { setActiveSprint, setSprints, setLoading, setError } = sprintSlice.actions;
export default sprintSlice.reducer;
