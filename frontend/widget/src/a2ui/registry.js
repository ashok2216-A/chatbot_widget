import {
  A2Row, A2Column, A2Card, A2List,
  A2Text, A2Image, A2Icon, A2Video, A2AudioPlayer, A2Content, A2Divider,
  A2Button, A2CheckBox, A2TextField, A2Slider, A2DateTimeInput, A2ChoicePicker,
  A2Tabs, A2Modal, A2Navigation,
} from './components';

/**
 * Maps component name strings (from the LLM JSON schema) to React components.
 * Keys are case-insensitive (lowercased at lookup time).
 */
export const COMPONENT_REGISTRY = {
  // Layout
  row:           A2Row,
  column:        A2Column,
  col:           A2Column,
  card:          A2Card,
  list:          A2List,
  // Content
  text:          A2Text,
  image:         A2Image,
  img:           A2Image,
  icon:          A2Icon,
  video:         A2Video,
  audioplayer:   A2AudioPlayer,
  audio:         A2AudioPlayer,
  content:       A2Content,
  divider:       A2Divider,
  separator:     A2Divider,
  // Input
  button:        A2Button,
  btn:           A2Button,
  checkbox:      A2CheckBox,
  check:         A2CheckBox,
  textfield:     A2TextField,
  input:         A2TextField,
  slider:        A2Slider,
  datetimeinput: A2DateTimeInput,
  datetime:      A2DateTimeInput,
  choicepicker:  A2ChoicePicker,
  select:        A2ChoicePicker,
  // Navigation
  tabs:          A2Tabs,
  modal:         A2Modal,
  navigation:    A2Navigation,
  nav:           A2Navigation,
};
