/**
 * Базовые пресеты UI-деревьев для строительной тематики (moscow.stroiapp.ru).
 * Каждый пресет — { id, title, desc, elements: UIElement[] }.
 * @typedef {import('../types/ui-builder').UIElement} UIElement
 */

let _n = 0;
const nid = () => `el-${++_n}`;

/** Карточка товара в стиле Технониколь: артикул + цена за м²/шт. @returns {UIElement[]} */
function productCard() {
  return [
    {
      id: nid(), type: "container", name: "Карточка товара",
      props: { className: "w-80 rounded-2xl bg-white shadow-xl overflow-hidden border border-neutral-200" },
      children: [
        { id: nid(), type: "image", name: "Фото товара", props: { className: "w-full h-48 object-cover", src: "https://placehold.co/640x400/e2e8f0/64748b?text=Товар" } },
        {
          id: nid(), type: "container", name: "Тело карточки", props: { className: "p-5 flex flex-col gap-2" },
          children: [
            { id: nid(), type: "text", name: "Артикул", props: { className: "text-xs text-neutral-400 font-mono tracking-wide", text: "Арт. ТН-ШИФ-001" } },
            { id: nid(), type: "text", name: "Название", props: { className: "text-base font-bold text-neutral-900 leading-snug", text: "Шифер волнистый Технониколь 1750×1130" } },
            {
              id: nid(), type: "container", name: "Цены", props: { className: "flex items-end justify-between mt-1" },
              children: [
                {
                  id: nid(), type: "container", name: "Цена блок", props: { className: "flex flex-col" },
                  children: [
                    { id: nid(), type: "text", name: "Цена за шт", props: { className: "text-2xl font-extrabold text-emerald-600", text: "385 ₽/шт" } },
                    { id: nid(), type: "text", name: "Цена за м²", props: { className: "text-xs text-neutral-500", text: "≈ 195 ₽/м²" } },
                  ],
                },
                { id: nid(), type: "button", name: "Кнопка купить", props: { className: "px-4 py-2 rounded-lg bg-emerald-600 text-white text-sm font-semibold hover:bg-emerald-700 transition", text: "В корзину" } },
              ],
            },
          ],
        },
      ],
    },
  ];
}

/** Калькулятор кубатуры фундамента. @returns {UIElement[]} */
function foundationCalc() {
  return [
    {
      id: nid(), type: "container", name: "Калькулятор фундамента",
      props: { className: "w-[26rem] rounded-2xl bg-neutral-900 text-white p-6 shadow-2xl border border-neutral-800" },
      children: [
        { id: nid(), type: "text", name: "Заголовок", props: { className: "text-lg font-bold mb-1", text: "Кубатура фундамента" } },
        { id: nid(), type: "text", name: "Подзаголовок", props: { className: "text-xs text-neutral-400 mb-4", text: "Рассчитайте объём бетона для ленточного фундамента" } },
        {
          id: nid(), type: "container", name: "Поля ввода", props: { className: "grid grid-cols-3 gap-3" },
          children: [
            { id: nid(), type: "input", name: "Длина", props: { className: "col-span-1 rounded-lg bg-neutral-800 border border-neutral-700 px-3 py-2 text-sm", placeholder: "Длина, м" } },
            { id: nid(), type: "input", name: "Ширина", props: { className: "col-span-1 rounded-lg bg-neutral-800 border border-neutral-700 px-3 py-2 text-sm", placeholder: "Ширина, м" } },
            { id: nid(), type: "input", name: "Высота", props: { className: "col-span-1 rounded-lg bg-neutral-800 border border-neutral-700 px-3 py-2 text-sm", placeholder: "Высота, м" } },
          ],
        },
        {
          id: nid(), type: "container", name: "Результат", props: { className: "mt-4 flex items-center justify-between rounded-xl bg-neutral-800 px-4 py-3" },
          children: [
            { id: nid(), type: "text", name: "Метка результата", props: { className: "text-sm text-neutral-300", text: "Объём бетона" } },
            { id: nid(), type: "text", name: "Значение", props: { className: "text-xl font-extrabold text-emerald-400", text: "12.6 м³" } },
          ],
        },
        { id: nid(), type: "button", name: "Кнопка расчёта", props: { className: "mt-4 w-full rounded-lg bg-emerald-600 py-2.5 text-sm font-semibold hover:bg-emerald-500 transition", text: "Рассчитать" } },
      ],
    },
  ];
}

/** Bento-сетка промо-баннеров. @returns {UIElement[]} */
function bentoPromo() {
  return [
    {
      id: nid(), type: "container", name: "Bento-сетка",
      props: { className: "w-[42rem] grid grid-cols-3 grid-rows-2 gap-4" },
      children: [
        {
          id: nid(), type: "container", name: "Главный баннер", props: { className: "col-span-2 row-span-2 rounded-2xl bg-gradient-to-br from-emerald-600 to-teal-700 p-6 flex flex-col justify-end text-white" },
          children: [
            { id: nid(), type: "text", name: "Заголовок баннера", props: { className: "text-2xl font-extrabold", text: "Цемент оптом от 320 ₽/мешок" } },
            { id: nid(), type: "text", name: "Подпись", props: { className: "text-sm text-emerald-100 mt-1", text: "Доставка по Москве и МО за 24 часа" } },
            { id: nid(), type: "button", name: "CTA", props: { className: "mt-4 w-max rounded-lg bg-white text-emerald-700 px-4 py-2 text-sm font-bold", text: "Смотреть каталог" } },
          ],
        },
        {
          id: nid(), type: "container", name: "Баннер инструменты", props: { className: "rounded-2xl bg-neutral-800 p-4 flex flex-col justify-center text-white border border-neutral-700" },
          children: [
            { id: nid(), type: "text", name: "Заголовок", props: { className: "text-sm font-bold", text: "Инструменты" } },
            { id: nid(), type: "text", name: "Подпись", props: { className: "text-xs text-neutral-400", text: "Скидки до −30%" } },
          ],
        },
        {
          id: nid(), type: "container", name: "Баннер доставка", props: { className: "rounded-2xl bg-amber-500 p-4 flex flex-col justify-center text-neutral-900" },
          children: [
            { id: nid(), type: "text", name: "Заголовок", props: { className: "text-sm font-bold", text: "Бесплатная доставка" } },
            { id: nid(), type: "text", name: "Подпись", props: { className: "text-xs", text: "от 50 000 ₽" } },
          ],
        },
      ],
    },
  ];
}

export const BUILDER_PRESETS = [
  { id: "product-card", title: "Карточка товара", desc: "Артикул + цена за шт/м²", build: productCard },
  { id: "foundation-calc", title: "Калькулятор фундамента", desc: "Кубатура бетона", build: foundationCalc },
  { id: "bento-promo", title: "Bento промо-сетка", desc: "Баннеры и акции", build: bentoPromo },
];
