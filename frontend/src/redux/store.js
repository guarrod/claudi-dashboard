import { configureStore } from '@reduxjs/toolkit';
import authReducer from './slices/authSlice';
import sprintReducer from './slices/sprintSlice';
import transactionReducer from './slices/transactionSlice';
import uiReducer from './slices/uiSlice';

const store = configureStore({
  reducer: {
    auth: authReducer,
    sprint: sprintReducer,
    transaction: transactionReducer,
    ui: uiReducer,
  },
});

export default store;
