/**
 * Канонические типы AI UI Builder.
 * Проект на JSX — этот .ts файл служит источником типов (type-only).
 * В JS-компонентах те же формы описаны через JSDoc @typedef.
 */

export type ComponentType = 'container' | 'button' | 'text' | 'image' | 'input';

export interface UIElementProps {
  className: string;
  text?: string;
  src?: string;
  placeholder?: string;
}

export interface UIElement {
  id: string;
  type: ComponentType;
  name: string;
  props: UIElementProps;
  children?: UIElement[];
}
