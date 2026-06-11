import React from 'react';
import { createBottomTabNavigator } from '@react-navigation/bottom-tabs';
import { createNativeStackNavigator } from '@react-navigation/native-stack';
import { Ionicons } from '@expo/vector-icons';
import DashboardScreen from '../screens/app/DashboardScreen';
import SprintScreen from '../screens/app/SprintScreen';
import NotificationsScreen from '../screens/app/NotificationsScreen';
import SavingsScreen from '../screens/app/SavingsScreen';
import TemplatesScreen from '../screens/app/TemplatesScreen';
import SettingsScreen from '../screens/app/SettingsScreen';

const Tab = createBottomTabNavigator();
const Stack = createNativeStackNavigator();

const DashboardStack = () => (
  <Stack.Navigator
    screenOptions={{
      headerShown: true,
      headerTitle: 'Dashboard',
    }}
  >
    <Stack.Screen name="DashboardHome" component={DashboardScreen} />
  </Stack.Navigator>
);

const SprintStack = () => (
  <Stack.Navigator
    screenOptions={{
      headerShown: true,
      headerTitle: 'Sprints',
    }}
  >
    <Stack.Screen name="SprintHome" component={SprintScreen} />
    <Stack.Screen
      name="Templates"
      component={TemplatesScreen}
      options={{ headerTitle: 'Plantillas' }}
    />
  </Stack.Navigator>
);

const NotificationsStack = () => (
  <Stack.Navigator
    screenOptions={{
      headerShown: true,
      headerTitle: 'Notificaciones',
    }}
  >
    <Stack.Screen name="NotificationsHome" component={NotificationsScreen} />
  </Stack.Navigator>
);

const SavingsStack = () => (
  <Stack.Navigator
    screenOptions={{
      headerShown: true,
      headerTitle: 'Ahorros',
    }}
  >
    <Stack.Screen name="SavingsHome" component={SavingsScreen} />
  </Stack.Navigator>
);

const SettingsStack = () => (
  <Stack.Navigator
    screenOptions={{
      headerShown: true,
      headerTitle: 'Configuración',
    }}
  >
    <Stack.Screen name="SettingsHome" component={SettingsScreen} />
    <Stack.Screen
      name="Templates"
      component={TemplatesScreen}
      options={{ headerTitle: 'Plantillas' }}
    />
  </Stack.Navigator>
);

const AppNavigator = () => {
  return (
    <Tab.Navigator
      screenOptions={({ route }) => ({
        tabBarIcon: ({ focused, color, size }) => {
          let iconName;
          if (route.name === 'Dashboard') {
            iconName = focused ? 'home' : 'home-outline';
          } else if (route.name === 'Sprint') {
            iconName = focused ? 'list' : 'list-outline';
          } else if (route.name === 'Notifications') {
            iconName = focused ? 'notifications' : 'notifications-outline';
          } else if (route.name === 'Savings') {
            iconName = focused ? 'cash' : 'cash-outline';
          } else if (route.name === 'Settings') {
            iconName = focused ? 'settings' : 'settings-outline';
          }
          return <Ionicons name={iconName} size={size} color={color} />;
        },
        tabBarActiveTintColor: '#007AFF',
        tabBarInactiveTintColor: '#999',
        headerShown: false,
      })}
    >
      <Tab.Screen
        name="Dashboard"
        component={DashboardStack}
        options={{ tabBarLabel: 'Dashboard' }}
      />
      <Tab.Screen
        name="Sprint"
        component={SprintStack}
        options={{ tabBarLabel: 'Sprint' }}
      />
      <Tab.Screen
        name="Notifications"
        component={NotificationsStack}
        options={{ tabBarLabel: 'Alertas' }}
      />
      <Tab.Screen
        name="Savings"
        component={SavingsStack}
        options={{ tabBarLabel: 'Ahorros' }}
      />
      <Tab.Screen
        name="Settings"
        component={SettingsStack}
        options={{ tabBarLabel: 'Config' }}
      />
    </Tab.Navigator>
  );
};

export default AppNavigator;
