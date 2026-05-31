import { createSlice } from '@reduxjs/toolkit';

const initialState = {
  theme: 'LIGHT', // LIGHT, DARK, SYSTEM
  completionMethod: 'CHECKBOX', // CHECKBOX, SLIDE, BOTH
  requiresConfirmation: true,
};

const uiSlice = createSlice({
  name: 'ui',
  initialState,
  reducers: {
    setTheme: (state, action) => {
      state.theme = action.payload;
    },
    setCompletionMethod: (state, action) => {
      state.completionMethod = action.payload;
    },
    setRequiresConfirmation: (state, action) => {
      state.requiresConfirmation = action.payload;
    },
  },
});

export const { setTheme, setCompletionMethod, setRequiresConfirmation } = uiSlice.actions;
export default uiSlice.reducer;
